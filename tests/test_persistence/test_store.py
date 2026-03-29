"""Tests unitarios para persistence/store.py.

Cubre:
- 4.1: save_rejected + get_decided_post_ids excluye posts rechazados
- 4.2: save_pending_delivery + get_pending_deliveries preserva opportunity_data
- 4.3: mark_sent transiciona pending_delivery → sent y get_decided_post_ids lo incluye
- 4.4: upsert maneja post_id duplicado sin error (UNIQUE constraint)
- 4.5: lógica de exclusión+recorte: 12 candidatos con 3 decididos → 8 más recientes sin decidir
- 4.6: post no seleccionado no genera efecto secundario en persistencia
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from auto_reddit.persistence.store import CandidateStore
from auto_reddit.shared.contracts import PostDecision, RedditCandidate


# ---------------------------------------------------------------------------
# Fixture: in-memory store (shared across tests in this module)
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path) -> CandidateStore:
    """CandidateStore respaldado por SQLite en memoria (via archivo temporal)."""
    s = CandidateStore(str(tmp_path / "test.db"))
    s.init_db()
    return s


# ---------------------------------------------------------------------------
# 4.1 — save_rejected + get_decided_post_ids excluye rechazados
# Spec scenario: filter eligible set
# ---------------------------------------------------------------------------


class TestSaveRejected:
    def test_rejected_post_appears_in_decided_ids(self, store):
        store.save_rejected("post_abc")
        decided = store.get_decided_post_ids()
        assert "post_abc" in decided

    def test_multiple_rejected_posts_all_appear(self, store):
        store.save_rejected("post_1")
        store.save_rejected("post_2")
        store.save_rejected("post_3")
        decided = store.get_decided_post_ids()
        assert {"post_1", "post_2", "post_3"}.issubset(decided)

    def test_undecided_post_not_in_decided_ids(self, store):
        store.save_rejected("post_decided")
        decided = store.get_decided_post_ids()
        assert "post_undecided" not in decided

    def test_rejected_status_is_stored_correctly(self, store):
        store.save_rejected("post_x")
        records = store.get_pending_deliveries()
        # rejected posts do not appear in pending_deliveries
        assert all(r.post_id != "post_x" for r in records)


# ---------------------------------------------------------------------------
# 4.2 — save_pending_delivery + get_pending_deliveries preserva opportunity_data
# Spec scenario: retry Telegram after prior AI acceptance (no re-evaluation)
# ---------------------------------------------------------------------------


class TestSavePendingDelivery:
    def test_pending_delivery_record_returned_with_opportunity_data(self, store):
        opportunity_json = '{"title": "Odoo partner opportunity", "score": 0.9}'
        store.save_pending_delivery("post_abc", opportunity_json)
        records = store.get_pending_deliveries()
        assert len(records) == 1
        record = records[0]
        assert record.post_id == "post_abc"
        assert record.status == PostDecision.pending_delivery
        assert record.opportunity_data == opportunity_json

    def test_pending_delivery_not_in_decided_ids(self, store):
        """pending_delivery posts remain eligible — not in get_decided_post_ids."""
        store.save_pending_delivery("post_pd", '{"data": "x"}')
        decided = store.get_decided_post_ids()
        assert "post_pd" not in decided

    def test_multiple_pending_deliveries_returned(self, store):
        store.save_pending_delivery("post_1", '{"a": 1}')
        store.save_pending_delivery("post_2", '{"b": 2}')
        records = store.get_pending_deliveries()
        post_ids = {r.post_id for r in records}
        assert post_ids == {"post_1", "post_2"}

    def test_opportunity_data_survives_roundtrip(self, store):
        """opportunity_data es devuelto exactamente como fue guardado (retry sin re-evaluar IA)."""
        data = '{"title": "Test", "score": 0.95, "subreddit": "Odoo"}'
        store.save_pending_delivery("post_retry", data)
        records = store.get_pending_deliveries()
        assert records[0].opportunity_data == data


# ---------------------------------------------------------------------------
# 4.3 — mark_sent transiciona pending_delivery → sent
# Spec scenario: close a post only on delivery success
# ---------------------------------------------------------------------------


class TestMarkSent:
    def test_mark_sent_transitions_status(self, store):
        store.save_pending_delivery("post_tg", '{"x": 1}')
        store.mark_sent("post_tg")

        # No longer in pending_deliveries
        pending = store.get_pending_deliveries()
        assert all(r.post_id != "post_tg" for r in pending)

    def test_sent_post_appears_in_decided_ids(self, store):
        store.save_pending_delivery("post_tg", '{"x": 1}')
        store.mark_sent("post_tg")
        decided = store.get_decided_post_ids()
        assert "post_tg" in decided

    def test_delivery_failure_does_not_mark_sent(self, store):
        """Si Telegram falla, el post permanece en pending_delivery (no se llama mark_sent)."""
        store.save_pending_delivery("post_fail", '{"y": 2}')
        # Simula fallo: NO llamamos mark_sent
        pending = store.get_pending_deliveries()
        assert any(r.post_id == "post_fail" for r in pending)
        decided = store.get_decided_post_ids()
        assert "post_fail" not in decided


# ---------------------------------------------------------------------------
# 4.4 — Upsert maneja post_id duplicado sin error (UNIQUE constraint)
# ---------------------------------------------------------------------------


class TestUpsert:
    def test_duplicate_rejected_insert_no_error(self, store):
        store.save_rejected("post_dup")
        store.save_rejected("post_dup")  # second insert → upsert, no exception
        decided = store.get_decided_post_ids()
        assert "post_dup" in decided

    def test_duplicate_pending_delivery_no_error(self, store):
        store.save_pending_delivery("post_dup", '{"v": 1}')
        store.save_pending_delivery("post_dup", '{"v": 2}')  # upsert, no exception
        records = store.get_pending_deliveries()
        # Only one record; latest opportunity_data wins
        matching = [r for r in records if r.post_id == "post_dup"]
        assert len(matching) == 1
        assert matching[0].opportunity_data == '{"v": 2}'

    def test_second_save_pending_preserves_original_decided_at(self, store):
        """Opción C: un segundo save_pending_delivery NO sobreescribe decided_at.

        La marca temporal de la primera decisión IA debe permanecer intacta
        incluso si el flujo de entrega reintenta el upsert en el siguiente ciclo.
        """
        import time as _time

        store.save_pending_delivery("post_retry", '{"v": 1}')
        first_records = store.get_pending_deliveries()
        original_decided_at = next(
            r.decided_at for r in first_records if r.post_id == "post_retry"
        )

        # Forzamos un timestamp diferente esperando al menos 1 segundo.
        # En tests rápidos usamos monkeypatch sobre time.time para no depender de sleep.
        import auto_reddit.persistence.store as store_module

        original_time = store_module.time.time
        try:
            store_module.time.time = lambda: original_decided_at + 60  # +60 segundos
            store.save_pending_delivery("post_retry", '{"v": 2}')
        finally:
            store_module.time.time = original_time

        second_records = store.get_pending_deliveries()
        matching = [r for r in second_records if r.post_id == "post_retry"]
        assert len(matching) == 1
        # opportunity_data debe haber cambiado (comportamiento de reintento)
        assert matching[0].opportunity_data == '{"v": 2}'
        # decided_at NO debe haber cambiado (opción C)
        assert matching[0].decided_at == original_decided_at

    def test_rejected_then_pending_upserts_correctly(self, store):
        store.save_rejected("post_x")
        store.save_pending_delivery("post_x", '{"new": true}')
        # Now status is pending_delivery; not in decided_ids
        decided = store.get_decided_post_ids()
        assert "post_x" not in decided
        pending = store.get_pending_deliveries()
        assert any(r.post_id == "post_x" for r in pending)


# ---------------------------------------------------------------------------
# 4.5 — Pipeline: exclusión + recorte
# Spec scenario: filter and cut the eligible set
# Given 12 candidates with 3 decided → result is 8 most recent undecided
# ---------------------------------------------------------------------------


def _make_candidate(post_id: str, created_utc: int) -> RedditCandidate:
    """Helper: crea un RedditCandidate mínimo para tests de pipeline."""
    return RedditCandidate(
        post_id=post_id,
        title=f"Post {post_id}",
        selftext="body",
        url=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        permalink=f"https://www.reddit.com/r/Odoo/comments/{post_id}/test/",
        author="testuser",
        subreddit="Odoo",
        created_utc=created_utc,
        source_api="reddit3",
    )


def _apply_pipeline_filter(
    candidates: list[RedditCandidate],
    decided_ids: set[str],
    daily_review_limit: int,
) -> list[RedditCandidate]:
    """Lógica de exclusión + recorte extraída de main.run() para tests unitarios."""
    eligible = [c for c in candidates if c.post_id not in decided_ids]
    eligible.sort(key=lambda c: c.created_utc, reverse=True)
    return eligible[:daily_review_limit]


class TestPipelineFilter:
    def test_12_candidates_3_decided_yields_8_most_recent_undecided(self, store):
        """Spec scenario: filter and cut the eligible set.

        12 candidatos totales, 3 con decisión final (sent+rejected) →
        los 8 más recientes sin decidir.
        """
        base_ts = 1_700_000_000
        # Posts post_00..post_11, post_00 is most recent (ts = base + 11*100)
        all_candidates = [
            _make_candidate(f"post_{i:02d}", base_ts + (11 - i) * 100)
            for i in range(12)
        ]

        # Decide on 3 posts (post_09 and post_10 rejected, post_11 sent via pending→sent)
        store.save_rejected("post_09")
        store.save_rejected("post_10")
        store.save_pending_delivery("post_11", '{"data": "x"}')
        store.mark_sent("post_11")

        decided_ids = store.get_decided_post_ids()
        review_set = _apply_pipeline_filter(all_candidates, decided_ids, 8)

        assert len(review_set) == 8
        # All returned posts are undecided
        assert all(c.post_id not in decided_ids for c in review_set)
        # Sorted by recency desc
        for i in range(len(review_set) - 1):
            assert review_set[i].created_utc >= review_set[i + 1].created_utc

    def test_12_candidates_3_decided_yields_8_most_recent_undecided_v2(self, store):
        """Versión sin helper interno — usa store directamente."""
        base_ts = 1_700_000_000
        all_candidates = [
            _make_candidate(f"post_{i:02d}", base_ts + (11 - i) * 100)
            for i in range(12)
        ]
        # Mark 3 as rejected
        store.save_rejected("post_09")
        store.save_rejected("post_10")
        store.save_rejected("post_11")

        decided_ids = store.get_decided_post_ids()
        review_set = _apply_pipeline_filter(all_candidates, decided_ids, 8)

        assert len(review_set) == 8
        assert "post_09" not in {c.post_id for c in review_set}
        assert "post_10" not in {c.post_id for c in review_set}
        assert "post_11" not in {c.post_id for c in review_set}
        # Most recent 8 of the remaining 9 undecided
        assert review_set[0].post_id == "post_00"

    def test_fewer_than_limit_returns_all_eligible(self, store):
        """Si hay menos candidatos elegibles que el límite, se devuelven todos."""
        candidates = [
            _make_candidate(f"post_{i}", 1_700_000_000 - i * 1000) for i in range(5)
        ]
        review_set = _apply_pipeline_filter(candidates, set(), 8)
        assert len(review_set) == 5

    def test_all_decided_returns_empty(self, store):
        """Si todos los candidatos tienen decisión final, el resultado es vacío."""
        candidates = [
            _make_candidate(f"post_{i}", 1_700_000_000 - i * 1000) for i in range(5)
        ]
        decided_ids = {c.post_id for c in candidates}
        review_set = _apply_pipeline_filter(candidates, decided_ids, 8)
        assert review_set == []


# ---------------------------------------------------------------------------
# 4.6 — Post no seleccionado no genera efecto secundario en persistencia
# Spec scenario: keep non-selected posts out of persistence
# ---------------------------------------------------------------------------


class TestNoSideEffectForNonSelected:
    def test_unselected_post_has_no_persistence_record(self, store):
        """Un post que no llega al pipeline de decisión no genera ningún registro."""
        decided = store.get_decided_post_ids()
        assert "post_not_selected" not in decided

        pending = store.get_pending_deliveries()
        assert all(r.post_id != "post_not_selected" for r in pending)

    def test_store_remains_empty_without_explicit_save(self, store):
        """El store vacío no contiene registros."""
        assert store.get_decided_post_ids() == set()
        assert store.get_pending_deliveries() == []
