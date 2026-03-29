"""Tests de integración para el façade deliver_daily().

Cubre:
- 4.4: Resumen enviado primero (no bloqueante si falla)
- 4.4: mark_sent llamado solo cuando Telegram confirma éxito
- 4.4: DeliveryReport conteos correctos
- 4.4: Scenario "Summary failure does not stop opportunity delivery"
- 4.4: Registros con opportunity_data inválido excluidos ANTES del cap (corrective)
- 4.4: Lista vacía → DeliveryReport vacío sin envíos
- corrective: deliver_daily acepta reviewed_post_count y lo pasa al resumen
- determinism: now_utc governa TTL/selección, retry/new y fecha del resumen con coherencia
"""

from __future__ import annotations

import datetime
import json
import time
from unittest.mock import MagicMock, call, patch

import pytest

from auto_reddit.delivery import deliver_daily
from auto_reddit.shared.contracts import (
    AcceptedOpportunity,
    DeliveryReport,
    OpportunityType,
    PostDecision,
    PostRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(cap: int = 8) -> MagicMock:
    settings = MagicMock()
    settings.telegram_bot_token = "BOT_TOKEN"
    settings.telegram_chat_id = "CHAT_ID"
    settings.max_daily_opportunities = cap
    return settings


def _make_opportunity_json(post_id: str = "abc123") -> str:
    opp = AcceptedOpportunity(
        post_id=post_id,
        title=f"Post {post_id}",
        link=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        post_language="en",
        opportunity_type=OpportunityType.funcionalidad,
        opportunity_reason="El hilo está sin respuesta.",
        post_summary_es="El usuario pregunta algo.",
        comment_summary_es="Sin respuestas.",
        suggested_response_es="Respuesta en español.",
        suggested_response_en="English answer.",
    )
    return opp.model_dump_json()


def _make_record(
    post_id: str,
    decided_at: int | None = None,
    opportunity_data: str | None = None,
) -> PostRecord:
    if decided_at is None:
        decided_at = int(time.time())
    if opportunity_data is None:
        opportunity_data = _make_opportunity_json(post_id)
    return PostRecord(
        post_id=post_id,
        status=PostDecision.pending_delivery,
        opportunity_data=opportunity_data,
        decided_at=decided_at,
    )


def _make_store(records: list[PostRecord]) -> MagicMock:
    store = MagicMock()
    store.get_pending_deliveries.return_value = records
    store.mark_sent = MagicMock()
    return store


# ---------------------------------------------------------------------------
# 4.4: Lista vacía → sin envíos, DeliveryReport vacío
# ---------------------------------------------------------------------------


class TestDeliverDailyEmptyQueue:
    def test_empty_pending_deliveries_sends_summary_no_opportunities(self):
        """
        Spec (updated): El resumen se emite SIEMPRE en cada ejecución de día laborable,
        incluso cuando la cola está vacía (0-opportunity run).
        No se envían mensajes individuales de oportunidades.
        """
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            report = deliver_daily(store, settings)

        # Se llama UNA vez: el resumen de 0 oportunidades
        mock_send.assert_called_once()
        store.mark_sent.assert_not_called()
        assert report.total_selected == 0
        assert report.sent_ok == 0
        assert report.sent_failed == 0
        # El resumen sí se envió
        assert report.summary_sent is True

    def test_empty_queue_report_is_delivery_report_instance(self):
        store = _make_store([])
        settings = _make_settings()
        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)
        assert isinstance(report, DeliveryReport)


# ---------------------------------------------------------------------------
# 4.4: Resumen enviado primero
# ---------------------------------------------------------------------------


class TestDeliverDailySummaryFirst:
    def test_summary_sent_before_opportunities(self):
        """El resumen se envía antes que las oportunidades individuales."""
        records = [_make_record("p1"), _make_record("p2")]
        store = _make_store(records)
        settings = _make_settings()
        call_order: list[str] = []

        def track_send(token, chat_id, text):
            if "del día" in text:
                call_order.append("summary")
            else:
                call_order.append("opportunity")
            return True

        with patch("auto_reddit.delivery.send_message", side_effect=track_send):
            report = deliver_daily(store, settings)

        # El primer envío debe ser el resumen
        assert call_order[0] == "summary"
        assert call_order.count("summary") == 1
        assert call_order.count("opportunity") == 2

    def test_summary_sent_flag_true_on_success(self):
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.summary_sent is True

    def test_summary_sent_flag_false_on_failure(self):
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        # Primer envío (resumen) falla, los siguientes tienen éxito
        call_count = [0]

        def summary_fails(token, chat_id, text):
            call_count[0] += 1
            if call_count[0] == 1:
                return False  # resumen falla
            return True  # oportunidades tienen éxito

        with patch("auto_reddit.delivery.send_message", side_effect=summary_fails):
            report = deliver_daily(store, settings)

        assert report.summary_sent is False


# ---------------------------------------------------------------------------
# 4.4: Scenario "Summary failure does not stop opportunity delivery"
# ---------------------------------------------------------------------------


class TestSummaryFailureNonBlocking:
    def test_summary_failure_does_not_block_opportunity_delivery(self):
        """
        Spec scenario: El fallo del resumen NO bloquea las entregas individuales.
        """
        records = [_make_record("p1"), _make_record("p2"), _make_record("p3")]
        store = _make_store(records)
        settings = _make_settings()
        call_count = [0]

        def summary_fails_rest_succeeds(token, chat_id, text):
            call_count[0] += 1
            if call_count[0] == 1:
                return False  # resumen falla
            return True  # oportunidades tienen éxito

        with patch(
            "auto_reddit.delivery.send_message", side_effect=summary_fails_rest_succeeds
        ):
            report = deliver_daily(store, settings)

        assert report.summary_sent is False
        # Las 3 oportunidades se enviaron igualmente
        assert report.sent_ok == 3
        assert report.sent_failed == 0
        # mark_sent llamado 3 veces
        assert store.mark_sent.call_count == 3

    def test_total_calls_includes_summary_plus_opportunities(self):
        """Total de llamadas a send_message = 1 (resumen) + N (oportunidades)."""
        n = 3
        records = [_make_record(f"p{i}") for i in range(n)]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings)

        assert mock_send.call_count == n + 1  # 1 resumen + n oportunidades


# ---------------------------------------------------------------------------
# 4.4: mark_sent llamado solo cuando Telegram confirma éxito
# ---------------------------------------------------------------------------


class TestMarkSentOnlyOnSuccess:
    def test_mark_sent_called_on_success(self):
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            deliver_daily(store, settings)

        store.mark_sent.assert_called_once_with("p1")

    def test_mark_sent_not_called_on_failure(self):
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        # Resumen = True (no bloqueante), oportunidad = False
        call_count = [0]

        def first_ok_rest_fail(token, chat_id, text):
            call_count[0] += 1
            if call_count[0] == 1:
                return True  # resumen ok
            return False  # oportunidad falla

        with patch("auto_reddit.delivery.send_message", side_effect=first_ok_rest_fail):
            report = deliver_daily(store, settings)

        store.mark_sent.assert_not_called()
        assert report.sent_failed == 1
        assert report.sent_ok == 0

    def test_mixed_success_and_failure(self):
        """mark_sent solo se llama para los mensajes que tuvieron éxito."""
        records = [_make_record("p1"), _make_record("p2"), _make_record("p3")]
        store = _make_store(records)
        settings = _make_settings()

        call_count = [0]

        def alternating(token, chat_id, text):
            call_count[0] += 1
            if call_count[0] == 1:
                return True  # resumen ok
            # p1 ok, p2 falla, p3 ok
            return call_count[0] % 2 == 0  # 2→True, 3→False, 4→True

        with patch("auto_reddit.delivery.send_message", side_effect=alternating):
            report = deliver_daily(store, settings)

        # Exactamente 2 éxitos (calls 2 y 4)
        assert report.sent_ok == 2
        assert report.sent_failed == 1
        assert store.mark_sent.call_count == 2


# ---------------------------------------------------------------------------
# 4.4: DeliveryReport conteos correctos
# ---------------------------------------------------------------------------


class TestDeliveryReportCounts:
    def test_report_total_selected_matches_selected_count(self):
        records = [_make_record(f"p{i}") for i in range(3)]
        store = _make_store(records)
        settings = _make_settings(cap=8)

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 3

    def test_report_sent_ok_all_success(self):
        records = [_make_record(f"p{i}") for i in range(4)]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.sent_ok == 4
        assert report.sent_failed == 0

    def test_report_sent_failed_all_fail(self):
        records = [_make_record(f"p{i}") for i in range(4)]
        store = _make_store(records)
        settings = _make_settings()

        call_count = [0]

        def first_ok_rest_fail(token, chat_id, text):
            call_count[0] += 1
            return call_count[0] == 1  # solo resumen ok

        with patch("auto_reddit.delivery.send_message", side_effect=first_ok_rest_fail):
            report = deliver_daily(store, settings)

        assert report.sent_ok == 0
        assert report.sent_failed == 4

    def test_expired_skipped_counted_in_report(self):
        """expired_skipped refleja registros expirados no seleccionados."""
        # Registros de hace 3 semanas → TTL expirado
        old_ts = int(time.time()) - 21 * 86400
        expired_records = [
            PostRecord(
                post_id=f"expired_{i}",
                status=PostDecision.pending_delivery,
                opportunity_data=_make_opportunity_json(f"expired_{i}"),
                decided_at=old_ts,
            )
            for i in range(3)
        ]
        valid_record = _make_record("valid")
        store = _make_store(expired_records + [valid_record])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.expired_skipped == 3
        assert report.total_selected == 1


# ---------------------------------------------------------------------------
# 4.4 corrective: Registros con opportunity_data inválido excluidos antes del cap
# ---------------------------------------------------------------------------


class TestInvalidOpportunityData:
    def test_invalid_json_excluded_before_cap_not_counted_as_selected(self):
        """
        Corrective: Registros con JSON malformado son excluidos en el selector,
        ANTES del cap. No se seleccionan ni aparecen en total_selected.
        """
        records = [
            _make_record("p_valid"),
            PostRecord(
                post_id="p_invalid",
                status=PostDecision.pending_delivery,
                opportunity_data="NOT VALID JSON",
                decided_at=int(time.time()),
            ),
        ]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        # Solo el registro válido se seleccionó y se envió
        assert report.total_selected == 1
        assert report.sent_ok == 1
        assert report.sent_failed == 0
        store.mark_sent.assert_called_once_with("p_valid")

    def test_invalid_json_does_not_consume_cap(self):
        """Registros inválidos no consumen cupo: cap=2 con 2 válidos y 1 inválido → 2 seleccionados."""
        records = [
            _make_record("p_good_1"),
            _make_record("p_good_2"),
            PostRecord(
                post_id="p_bad",
                status=PostDecision.pending_delivery,
                opportunity_data="{bad json}",
                decided_at=int(time.time()) - 100,
            ),
        ]
        store = _make_store(records)
        settings = _make_settings(cap=2)

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 2
        assert report.sent_ok == 2
        assert report.sent_failed == 0

    def test_cap_applied_correctly_in_facade(self):
        """El cap settings.max_daily_opportunities se aplica correctamente."""
        records = [_make_record(f"p{i}") for i in range(12)]
        store = _make_store(records)
        settings = _make_settings(cap=5)

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 5
        assert store.mark_sent.call_count == 5


# ---------------------------------------------------------------------------
# corrective: deliver_daily acepta reviewed_post_count y run_date
# ---------------------------------------------------------------------------


class TestDeliverDailyReviewedPostCount:
    """El façade debe aceptar reviewed_post_count y run_date para el resumen (product.md §10)."""

    def test_deliver_daily_accepts_reviewed_post_count(self):
        """deliver_daily no falla cuando se pasa reviewed_post_count."""
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            report = deliver_daily(store, settings, reviewed_post_count=8)

        assert report.total_selected == 1
        # El resumen enviado debe incluir el conteo de revisados
        first_call_text = mock_send.call_args_list[0][0][2]
        assert "8" in first_call_text
        assert "revisados" in first_call_text

    def test_deliver_daily_accepts_run_date(self):
        """deliver_daily no falla cuando se pasa run_date explícito."""
        import datetime

        fixed_date = datetime.date(2026, 3, 28)
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            report = deliver_daily(store, settings, run_date=fixed_date)

        first_call_text = mock_send.call_args_list[0][0][2]
        assert "28/03/2026" in first_call_text

    def test_deliver_daily_without_reviewed_post_count_still_works(self):
        """El parámetro es opcional; sin él la entrega funciona igualmente."""
        records = [_make_record("p1")]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 1
        assert report.sent_ok == 1


# ---------------------------------------------------------------------------
# 4.4: Spec scenario "Zero-opportunity weekday run still emits a summary"
# ---------------------------------------------------------------------------


class TestZeroOpportunitySummary:
    """Spec scenario: Un run de día laborable con 0 oportunidades aún emite resumen."""

    def test_empty_queue_emits_summary(self):
        """
        Spec scenario: Zero-opportunity weekday run still emits a summary.
        Con 0 candidatos seleccionados, el resumen de Telegram SE ENVÍA igualmente.
        """
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            report = deliver_daily(store, settings)

        # El resumen SE envía aunque no haya oportunidades
        mock_send.assert_called_once()  # solo la llamada del resumen
        assert report.summary_sent is True
        assert report.total_selected == 0
        assert report.sent_ok == 0

    def test_empty_queue_summary_contains_zero_count(self):
        """El resumen de 0 oportunidades incluye '0' en el texto."""
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings)

        summary_text = mock_send.call_args_list[0][0][2]
        assert "0" in summary_text

    def test_empty_queue_summary_sent_before_any_opportunity(self):
        """Con 0 candidatos, se emite exactamente 1 mensaje (solo el resumen)."""
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings)

        assert mock_send.call_count == 1

    def test_empty_queue_summary_failure_is_recorded(self):
        """Si el resumen de 0-oportunidades falla, summary_sent es False."""
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=False):
            report = deliver_daily(store, settings)

        assert report.summary_sent is False
        assert report.total_selected == 0


# ---------------------------------------------------------------------------
# 4.3: Spec scenarios "Runtime enforces configured cap" / "Lowering cap"
# ---------------------------------------------------------------------------


class TestDeliveryCapFromMaxDailyOpportunities:
    """Spec scenarios: cap governed by max_daily_opportunities (single cap)."""

    def test_cap_8_from_10_selects_8(self):
        """
        Spec scenario: max_daily_opportunities=8 y 10 candidatos → exactamente 8.
        """
        records = [_make_record(f"p{i}") for i in range(10)]
        store = _make_store(records)
        settings = _make_settings(cap=8)

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 8

    def test_cap_3_from_5_selects_3(self):
        """
        Spec scenario: max_daily_opportunities=3 y 5 candidatos → exactamente 3.
        """
        records = [_make_record(f"p{i}") for i in range(5)]
        store = _make_store(records)
        settings = _make_settings(cap=3)

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings)

        assert report.total_selected == 3


# ---------------------------------------------------------------------------
# Determinism: now_utc governa TTL, retry/new y fecha del resumen coherentemente
# ---------------------------------------------------------------------------

_UTC = datetime.timezone.utc


class TestNowUtcDeterminism:
    """now_utc es la única fuente de verdad temporal: TTL, clasificación y resumen
    deben derivar todos de la misma referencia lógica."""

    def _make_record_dt(self, post_id: str, decided_at: int) -> PostRecord:
        return PostRecord(
            post_id=post_id,
            status=PostDecision.pending_delivery,
            opportunity_data=_make_opportunity_json(post_id),
            decided_at=decided_at,
        )

    def test_now_utc_governs_summary_date(self):
        """El resumen usa la fecha derivada de now_utc, no datetime.now()."""
        fixed_now = datetime.datetime(2025, 6, 15, 10, 30, 0, tzinfo=_UTC)
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings, now_utc=fixed_now)

        summary_text = mock_send.call_args_list[0][0][2]
        assert "15/06/2025" in summary_text

    def test_now_utc_governs_ttl_filtering(self):
        """TTL usa el timestamp de now_utc: un registro expirado según now_utc no se selecciona."""
        # Registro creado el lunes 2025-06-09 → expira el viernes 2025-06-13 23:59:59 UTC
        monday_ts = int(
            datetime.datetime(2025, 6, 9, 12, 0, 0, tzinfo=_UTC).timestamp()
        )
        record = self._make_record_dt("p_expiry", monday_ts)

        # now_utc = sábado 14/06/2025 → el registro ya expiró
        saturday_now = datetime.datetime(2025, 6, 14, 8, 0, 0, tzinfo=_UTC)
        store = _make_store([record])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings, now_utc=saturday_now)

        assert report.total_selected == 0
        assert report.expired_skipped == 1

    def test_now_utc_governs_retry_vs_new_classification(self):
        """La clasificación retry/new usa today_start derivado de now_utc."""
        # now_utc = 2025-06-11 14:00 UTC (miércoles)
        fixed_now = datetime.datetime(2025, 6, 11, 14, 0, 0, tzinfo=_UTC)

        # Registro "retry": decided_at = martes → anterior al inicio de hoy
        retry_ts = int(
            datetime.datetime(2025, 6, 10, 10, 0, 0, tzinfo=_UTC).timestamp()
        )
        # Registro "new": decided_at = hoy mismo (miércoles) → >= today_start
        new_ts = int(datetime.datetime(2025, 6, 11, 10, 0, 0, tzinfo=_UTC).timestamp())

        records = [
            self._make_record_dt("p_retry", retry_ts),
            self._make_record_dt("p_new", new_ts),
        ]
        store = _make_store(records)
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True):
            report = deliver_daily(store, settings, now_utc=fixed_now)

        assert report.retries == 1
        assert report.new == 1

    def test_summary_date_matches_ttl_reference(self):
        """La fecha del resumen y el TTL usan la misma referencia temporal."""
        # now_utc = viernes 13/06/2025 23:50 — registro del lunes justo en el borde
        fixed_now = datetime.datetime(2025, 6, 13, 23, 50, 0, tzinfo=_UTC)
        monday_ts = int(
            datetime.datetime(2025, 6, 9, 12, 0, 0, tzinfo=_UTC).timestamp()
        )
        record = self._make_record_dt("p_border", monday_ts)

        store = _make_store([record])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            report = deliver_daily(store, settings, now_utc=fixed_now)

        # Aún no expirado: expiry=Vie 23:59:59, now=Vie 23:50
        assert report.total_selected == 1
        # El resumen muestra la fecha de now_utc (viernes 13/06/2025)
        summary_text = mock_send.call_args_list[0][0][2]
        assert "13/06/2025" in summary_text

    def test_run_date_compat_derives_now_utc(self):
        """run_date como alias construye now_utc = inicio del día dado (00:00:00 UTC)."""
        fixed_date = datetime.date(2025, 6, 11)
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings, run_date=fixed_date)

        summary_text = mock_send.call_args_list[0][0][2]
        assert "11/06/2025" in summary_text

    def test_now_utc_takes_precedence_over_run_date(self):
        """Si se pasan ambos, now_utc tiene precedencia sobre run_date."""
        now_utc = datetime.datetime(2025, 7, 4, 15, 0, 0, tzinfo=_UTC)
        run_date = datetime.date(2025, 1, 1)  # distinto — debe ignorarse
        store = _make_store([])
        settings = _make_settings()

        with patch("auto_reddit.delivery.send_message", return_value=True) as mock_send:
            deliver_daily(store, settings, now_utc=now_utc, run_date=run_date)

        summary_text = mock_send.call_args_list[0][0][2]
        assert "04/07/2025" in summary_text
        assert "01/01/2025" not in summary_text
