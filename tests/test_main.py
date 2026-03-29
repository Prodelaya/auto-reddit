"""Tests unitarios para main.py.

Cubre:
- 4.1: Guardia de fin de semana — Sábado y Domingo omiten el pipeline sin efectos secundarios
- 4.1: Días laborables (Lunes–Viernes) continúan con el pipeline normal
- Filtro is_complete — candidatos incompletos no entran a evaluación ni persistencia
"""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 4.1: Weekend guard (Spec scenarios: Weekend run is skipped cleanly / Weekday proceeds)
# ---------------------------------------------------------------------------


class TestWeekendGuard:
    """Spec scenarios para la guardia de fin de semana en main.run()."""

    def _patch_pipeline(self):
        """Contexto de parches para aislar el pipeline de efectos secundarios reales."""
        return [
            patch("auto_reddit.main.settings"),
            patch("auto_reddit.main.CandidateStore"),
            patch("auto_reddit.main.collect_candidates", return_value=[]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", return_value=[]),
            patch("auto_reddit.main.deliver_daily"),
        ]

    @pytest.mark.parametrize(
        "weekday,name",
        [
            (5, "Saturday"),
            (6, "Sunday"),
        ],
    )
    def test_weekend_run_returns_without_pipeline_side_effects(self, weekday, name):
        """
        Spec scenario: Weekend run is skipped cleanly.
        Un run de sábado o domingo termina antes de colección, evaluación y entrega.
        """
        from auto_reddit.main import run

        fixed_date = datetime.date(2026, 3, 28)  # Sábado
        # Build a date with the target weekday
        # weekday() 5=Sat, 6=Sun
        # Use a known Saturday: 2026-03-28 (weekday=5) and Sunday 2026-03-29 (weekday=6)
        if weekday == 5:
            target_date = datetime.date(2026, 3, 28)  # Saturday
        else:
            target_date = datetime.date(2026, 3, 29)  # Sunday

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.CandidateStore") as mock_store_cls,
            patch("auto_reddit.main.collect_candidates") as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts") as mock_fetch,
            patch("auto_reddit.main.evaluate_batch") as mock_eval,
            patch("auto_reddit.main.deliver_daily") as mock_deliver,
        ):
            mock_dt.date.today.return_value = target_date

            run()

        # Ningún efecto secundario debe ocurrir
        mock_store_cls.assert_not_called()
        mock_collect.assert_not_called()
        mock_fetch.assert_not_called()
        mock_eval.assert_not_called()
        mock_deliver.assert_not_called()

    @pytest.mark.parametrize(
        "weekday,target_date",
        [
            (0, datetime.date(2026, 3, 23)),  # Monday
            (1, datetime.date(2026, 3, 24)),  # Tuesday
            (2, datetime.date(2026, 3, 25)),  # Wednesday
            (3, datetime.date(2026, 3, 26)),  # Thursday
            (4, datetime.date(2026, 3, 27)),  # Friday
        ],
    )
    def test_weekday_run_proceeds_to_pipeline(self, weekday, target_date):
        """
        Spec scenario: Weekday run proceeds normally.
        De lunes a viernes, la guardia pasa y el pipeline se ejecuta.
        """
        from auto_reddit.main import run

        mock_settings = MagicMock()
        mock_settings.db_path = ":memory:"
        mock_settings.daily_review_limit = 8

        mock_store = MagicMock()
        mock_store.get_decided_post_ids.return_value = set()
        mock_store.get_pending_deliveries.return_value = []

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.CandidateStore", return_value=mock_store),
            patch(
                "auto_reddit.main.collect_candidates", return_value=[]
            ) as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", return_value=[]),
            patch(
                "auto_reddit.main.deliver_daily",
                return_value=MagicMock(
                    total_selected=0,
                    retries=0,
                    new=0,
                    sent_ok=0,
                    sent_failed=0,
                    summary_sent=True,
                    expired_skipped=0,
                ),
            ),
        ):
            mock_dt.date.today.return_value = target_date

            run()

        # collect_candidates debe haber sido llamado (el pipeline arrancó)
        mock_collect.assert_called_once()


# ---------------------------------------------------------------------------
# Filtro is_complete: candidatos incompletos no entran a evaluación/persistencia
# ---------------------------------------------------------------------------


def _make_candidate(**overrides):
    """Factoría de RedditCandidate con valores válidos por defecto."""
    from auto_reddit.shared.contracts import RedditCandidate

    defaults = dict(
        post_id="abc123",
        title="Need help with Odoo",
        url="https://reddit.com/r/Odoo/comments/abc123",
        permalink="https://reddit.com/r/Odoo/comments/abc123",
        author="user1",
        subreddit="Odoo",
        created_utc=1700000000,
        source_api="reddit34",
        selftext="Some body text",
    )
    defaults.update(overrides)
    return RedditCandidate(**defaults)


class TestIsCompleteFilter:
    """Candidatos con is_complete=False deben descartarse antes de evaluación y persistencia."""

    def _base_patches(self, mock_settings, mock_store):
        """Parches base para aislar main.run()."""
        return {
            "auto_reddit.main.settings": mock_settings,
            "auto_reddit.main.CandidateStore": lambda _: mock_store,
        }

    def _run_with_candidates(self, candidates, mock_settings=None, mock_store=None):
        """Ejecuta run() con la lista de candidatos dada y devuelve los mocks de evaluación/store."""
        from unittest.mock import MagicMock, call, patch

        import datetime

        from auto_reddit.main import run

        if mock_settings is None:
            mock_settings = MagicMock()
            mock_settings.db_path = ":memory:"
            mock_settings.daily_review_limit = 50

        if mock_store is None:
            mock_store = MagicMock()
            mock_store.get_decided_post_ids.return_value = set()

        mock_eval = MagicMock(return_value=[])
        mock_deliver = MagicMock(
            return_value=MagicMock(
                total_selected=0,
                retries=0,
                new=0,
                sent_ok=0,
                sent_failed=0,
                summary_sent=True,
                expired_skipped=0,
            )
        )

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.CandidateStore", return_value=mock_store),
            patch("auto_reddit.main.collect_candidates", return_value=candidates),
            patch(
                "auto_reddit.main.fetch_thread_contexts", return_value=[]
            ) as mock_fetch,
            patch("auto_reddit.main.evaluate_batch", mock_eval),
            patch("auto_reddit.main.deliver_daily", mock_deliver),
        ):
            mock_dt.date.today.return_value = datetime.date(2026, 3, 23)  # Monday
            run()

        return mock_eval, mock_fetch, mock_store

    def test_incomplete_candidate_does_not_reach_evaluate_batch(self):
        """
        Un candidato con is_complete=False no llega a evaluate_batch.
        fetch_thread_contexts y evaluate_batch reciben lista vacía.
        """
        incomplete = _make_candidate(selftext=None)  # is_complete=False
        assert not incomplete.is_complete  # pre-condición

        mock_eval, mock_fetch, _ = self._run_with_candidates([incomplete])

        # evaluate_batch recibe los thread_contexts (vacíos porque fetch no recibió nada)
        # La clave: fetch_thread_contexts se llama con review_set vacío
        mock_fetch.assert_called_once()
        passed_review_set = mock_fetch.call_args[0][0]
        assert passed_review_set == [], (
            f"review_set debería estar vacío, recibió: {passed_review_set}"
        )

    def test_incomplete_candidate_does_not_trigger_persistence(self):
        """
        Un candidato incompleto no genera llamadas a save_pending_delivery ni save_rejected
        cuando evaluate_batch no lo procesa.
        """
        incomplete = _make_candidate(author=None)  # is_complete=False
        assert not incomplete.is_complete

        _, _, mock_store = self._run_with_candidates([incomplete])

        mock_store.save_pending_delivery.assert_not_called()
        mock_store.save_rejected.assert_not_called()

    def test_complete_candidate_reaches_fetch_thread_contexts(self):
        """
        Un candidato con is_complete=True pasa el filtro y llega a fetch_thread_contexts.
        """
        complete = _make_candidate()
        assert complete.is_complete  # pre-condición

        _, mock_fetch, _ = self._run_with_candidates([complete])

        mock_fetch.assert_called_once()
        passed_review_set = mock_fetch.call_args[0][0]
        assert len(passed_review_set) == 1
        assert passed_review_set[0].post_id == "abc123"

    def test_mixed_candidates_only_complete_pass(self):
        """
        Con candidatos mezclados, solo los completos llegan a fetch_thread_contexts.
        """
        complete1 = _make_candidate(post_id="ok1", title="Valid post 1")
        complete2 = _make_candidate(post_id="ok2", title="Valid post 2")
        incomplete1 = _make_candidate(post_id="bad1", selftext=None)
        incomplete2 = _make_candidate(post_id="bad2", author=None)

        assert complete1.is_complete
        assert complete2.is_complete
        assert not incomplete1.is_complete
        assert not incomplete2.is_complete

        _, mock_fetch, _ = self._run_with_candidates(
            [complete1, incomplete1, complete2, incomplete2]
        )

        passed_review_set = mock_fetch.call_args[0][0]
        passed_ids = {c.post_id for c in passed_review_set}
        assert passed_ids == {"ok1", "ok2"}, (
            f"Solo deben pasar los completos, pasaron: {passed_ids}"
        )

    def test_empty_post_id_candidate_does_not_reach_pipeline(self):
        """
        Un candidato con post_id vacío (is_complete=False) no llega al pipeline.
        Este es el caso más crítico: post_id vacío rompe la PRIMARY KEY de SQLite.
        """
        # post_id="" + otros campos completos → is_complete=False
        incomplete = _make_candidate(post_id="")
        assert not incomplete.is_complete

        _, mock_fetch, mock_store = self._run_with_candidates([incomplete])

        passed_review_set = mock_fetch.call_args[0][0]
        assert passed_review_set == []
        mock_store.save_pending_delivery.assert_not_called()
        mock_store.save_rejected.assert_not_called()
