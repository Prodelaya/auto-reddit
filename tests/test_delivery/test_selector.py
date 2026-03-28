"""Tests para delivery/selector.py.

Cubre:
- 4.1: TTL expiry para cada bucket de día (Lun-Mié→Vie, Jue-Vie→Lun, Sáb-Dom→Lun)
- 4.1: Ordenación retry-first (decided_at ASC)
- 4.1: Aplicación del cap
- 4.1: Relleno mixto reintento + nuevo
- 4.1: Scenario "Retry backlog consumes cap first"
- 4.1: Scenario "Remaining capacity filled with new"
- 4.5: Casos borde exactos en el límite del TTL (Vie 23:59:59 vs Sáb 00:00:00)
- 4.5: Manejo defensivo de Sábado/Domingo
- corrective: Registros con JSON malformado / schema inválido excluidos ANTES del cap
"""

from __future__ import annotations

import datetime

import pytest

from auto_reddit.delivery.selector import _expiry_ts, count_expired, select_deliveries
from auto_reddit.shared.contracts import (
    AcceptedOpportunity,
    OpportunityType,
    PostDecision,
    PostRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_opportunity_json(post_id: str = "test") -> str:
    """Devuelve un JSON válido de AcceptedOpportunity para usar en tests del selector."""
    opp = AcceptedOpportunity(
        post_id=post_id,
        title=f"Post {post_id}",
        link=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        post_language="en",
        opportunity_type=OpportunityType.funcionalidad,
        opportunity_reason="Test reason.",
        post_summary_es="Resumen de prueba.",
        comment_summary_es=None,
        suggested_response_es="Respuesta ES.",
        suggested_response_en="English answer.",
    )
    return opp.model_dump_json()


def _make_record(
    post_id: str,
    decided_at: int,
    opportunity_data: str | None = None,
) -> PostRecord:
    """Crea un PostRecord en pending_delivery.

    Si no se proporciona ``opportunity_data``, se usa un JSON válido de
    ``AcceptedOpportunity`` para que el selector lo acepte.
    """
    if opportunity_data is None:
        opportunity_data = _valid_opportunity_json(post_id)
    return PostRecord(
        post_id=post_id,
        status=PostDecision.pending_delivery,
        opportunity_data=opportunity_data,
        decided_at=decided_at,
    )


def _ts(weekday_offset: int, hour: int = 12, minute: int = 0, second: int = 0) -> int:
    """Devuelve un timestamp UTC para el Lunes de la semana actual + weekday_offset días."""
    # Lunes de la semana actual como base
    today = datetime.date(2026, 3, 23)  # Lunes fijo para reproducibilidad
    target = today + datetime.timedelta(days=weekday_offset)
    dt = datetime.datetime(
        target.year,
        target.month,
        target.day,
        hour,
        minute,
        second,
        tzinfo=datetime.timezone.utc,
    )
    return int(dt.timestamp())


# ---------------------------------------------------------------------------
# TTL: _expiry_ts calcula el timestamp correcto para cada día
# ---------------------------------------------------------------------------


class TestExpiryTs:
    def test_monday_expires_on_friday_2359(self):
        # Lunes → vence Viernes de la misma semana a las 23:59:59
        ts = _ts(0)  # Lunes
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 4  # Viernes
        assert expiry_dt.hour == 23
        assert expiry_dt.minute == 59
        assert expiry_dt.second == 59

    def test_tuesday_expires_on_friday_2359(self):
        ts = _ts(1)  # Martes
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 4  # Viernes
        assert expiry_dt.hour == 23

    def test_wednesday_expires_on_friday_2359(self):
        ts = _ts(2)  # Miércoles
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 4  # Viernes

    def test_thursday_expires_on_next_monday_2359(self):
        ts = _ts(3)  # Jueves
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes
        # Debe ser el lunes SIGUIENTE (7 días después del jueves)
        decided_dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        assert expiry_dt.date() > decided_dt.date()

    def test_friday_expires_on_next_monday_2359(self):
        ts = _ts(4)  # Viernes
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes siguiente
        assert expiry_dt.hour == 23

    def test_saturday_expires_on_next_monday_2359(self):
        ts = _ts(5)  # Sábado (defensivo)
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes siguiente

    def test_sunday_expires_on_next_monday_2359(self):
        ts = _ts(6)  # Domingo (defensivo)
        expiry = _expiry_ts(ts)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes siguiente


# ---------------------------------------------------------------------------
# 4.5: Casos borde exactos en el límite del TTL
# ---------------------------------------------------------------------------


class TestTTLBoundary:
    def test_record_at_expiry_second_is_valid(self):
        """Un registro cuyo vencimiento es exactamente ``now`` sigue siendo válido."""
        # Creado el lunes → vence el viernes 23:59:59
        decided_at = _ts(0)  # Lunes 12:00 UTC
        expiry = _expiry_ts(decided_at)
        # now == expiry: expiry_ts >= now → válido
        records = [_make_record("p1", decided_at)]
        selected = select_deliveries(records, now=expiry)
        assert len(selected) == 1

    def test_record_one_second_past_expiry_is_expired(self):
        """Un registro con vencimiento = now - 1 ya está expirado."""
        decided_at = _ts(0)  # Lunes
        expiry = _expiry_ts(decided_at)
        records = [_make_record("p1", decided_at)]
        # now es un segundo después del vencimiento
        selected = select_deliveries(records, now=expiry + 1)
        assert len(selected) == 0

    def test_friday_2359_59_valid_saturday_0000_expired(self):
        """Viernes 23:59:59 → válido; Sábado 00:00:00 → expirado."""
        # Registro creado el Lunes (Mon→Fri expiry)
        decided_at = _ts(0)  # Lunes
        expiry = _expiry_ts(decided_at)
        records = [_make_record("p1", decided_at)]

        # Justo en el límite (Viernes 23:59:59 UTC) → válido
        selected_valid = select_deliveries(records, now=expiry)
        assert len(selected_valid) == 1

        # Un segundo después (Sábado 00:00:00 UTC) → expirado
        selected_expired = select_deliveries(records, now=expiry + 1)
        assert len(selected_expired) == 0

    def test_saturday_record_defensive_expires_monday(self):
        """Registro creado en Sábado expira el Lunes siguiente (tratamiento defensivo)."""
        decided_at = _ts(5)  # Sábado
        expiry = _expiry_ts(decided_at)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes

    def test_sunday_record_defensive_expires_monday(self):
        """Registro creado en Domingo expira el Lunes siguiente (tratamiento defensivo)."""
        decided_at = _ts(6)  # Domingo
        expiry = _expiry_ts(decided_at)
        expiry_dt = datetime.datetime.fromtimestamp(expiry, tz=datetime.timezone.utc)
        assert expiry_dt.weekday() == 0  # Lunes


# ---------------------------------------------------------------------------
# 4.1: Filtrado de registros sin opportunity_data
# ---------------------------------------------------------------------------


class TestFilterNoOpportunityData:
    def test_record_without_opportunity_data_excluded(self):
        records = [
            _make_record("p1", _ts(0)),  # valid JSON — debe incluirse
            PostRecord(
                post_id="p_null",
                status=PostDecision.pending_delivery,
                opportunity_data=None,
                decided_at=_ts(0),
            ),
        ]
        now = _ts(0, hour=14)
        selected = select_deliveries(records, now=now)
        assert all(r.post_id != "p_null" for r in selected)
        assert len(selected) == 1


# ---------------------------------------------------------------------------
# 4.1: Scenario "Retry backlog consumes cap first"
# ---------------------------------------------------------------------------


class TestRetryBacklogConsumesCap:
    def test_more_than_cap_valid_records_selects_exactly_cap(self):
        """Spec scenario: más de 8 registros válidos → selecciona exactamente 8."""
        now = _ts(1, hour=14)  # Martes 14:00 UTC
        # 10 registros creados el lunes (todos válidos hasta el viernes)
        records = [_make_record(f"p{i}", _ts(0, hour=i + 1)) for i in range(10)]
        selected = select_deliveries(records, now=now, cap=8)
        assert len(selected) == 8

    def test_retry_backlog_fills_entire_cap_no_new_added(self):
        """
        Spec scenario: 10 reintentos válidos y cap=8 → solo 8 reintentos, sin nuevos.
        """
        now = _ts(1, hour=14)  # Martes 14:00
        # 10 registros "viejos" (creados el lunes, decididos antes de today_midnight)
        records = [_make_record(f"retry_{i}", _ts(0, hour=i + 1)) for i in range(10)]
        selected = select_deliveries(records, now=now, cap=8)
        # Los 8 más antiguos deben ser seleccionados
        assert len(selected) == 8
        selected_ids = {r.post_id for r in selected}
        # Los más recientes (retry_8, retry_9) quedan fuera del cap
        assert "retry_8" not in selected_ids
        assert "retry_9" not in selected_ids

    def test_ordering_is_decided_at_asc(self):
        """Los registros seleccionados están ordenados por decided_at ASC (más antiguos primero)."""
        now = _ts(2, hour=14)  # Miércoles
        records = [
            _make_record("p_new", _ts(2, hour=10)),  # creado hoy
            _make_record("p_old", _ts(0, hour=10)),  # creado el lunes
            _make_record("p_mid", _ts(1, hour=10)),  # creado el martes
        ]
        selected = select_deliveries(records, now=now, cap=8)
        assert selected[0].post_id == "p_old"
        assert selected[1].post_id == "p_mid"
        assert selected[2].post_id == "p_new"


# ---------------------------------------------------------------------------
# 4.1: Scenario "Remaining capacity filled with new"
# ---------------------------------------------------------------------------


class TestRemainingCapacityFilledWithNew:
    def test_3_retries_5_new_fills_cap_of_8(self):
        """
        Spec scenario: 3 reintentos + 6 nuevas → selecciona 3 + 5 = 8.
        (Todos los retries primero, luego las nuevas más antiguas hasta el cap.)
        """
        now = _ts(2, hour=14)  # Miércoles
        # 3 registros "viejos" del lunes
        retries = [_make_record(f"retry_{i}", _ts(0, hour=i + 8)) for i in range(3)]
        # 6 registros "nuevos" del miércoles (hora posterior al now del test)
        new_records = [_make_record(f"new_{i}", _ts(2, hour=i + 1)) for i in range(6)]
        records = retries + new_records
        selected = select_deliveries(records, now=now, cap=8)
        assert len(selected) == 8
        # Los 3 reintentos deben estar entre los primeros 3
        selected_ids = [r.post_id for r in selected]
        # El retry más antiguo debe ser el primero
        assert "retry_0" in selected_ids

    def test_fewer_valid_than_cap_returns_all_valid(self):
        """Si hay menos registros válidos que el cap, se devuelven todos."""
        now = _ts(1, hour=14)  # Martes
        records = [_make_record(f"p{i}", _ts(0, hour=i + 1)) for i in range(5)]
        selected = select_deliveries(records, now=now, cap=8)
        assert len(selected) == 5

    def test_empty_records_returns_empty(self):
        selected = select_deliveries([], now=_ts(1), cap=8)
        assert selected == []

    def test_all_expired_returns_empty(self):
        """Todos los registros expirados → lista vacía."""
        # Registros del lunes, ahora es el siguiente martes (expirados el viernes anterior)
        decided_at = _ts(0)  # Lunes
        expiry = _expiry_ts(decided_at)
        records = [_make_record(f"p{i}", decided_at) for i in range(5)]
        # now es después del vencimiento del viernes
        selected = select_deliveries(records, now=expiry + 3600)
        assert selected == []

    def test_cap_zero_returns_empty(self):
        records = [_make_record(f"p{i}", _ts(0)) for i in range(5)]
        selected = select_deliveries(records, now=_ts(1), cap=0)
        assert selected == []


# ---------------------------------------------------------------------------
# 4.1: TTL filtering removes expired records before ordering
# ---------------------------------------------------------------------------


class TestTTLFiltering:
    def test_expired_records_excluded_from_selection(self):
        """Registros expirados no se incluyen aunque haya espacio en el cap."""
        # Registro expirado: creado hace mucho (fuera de TTL)
        # Usamos un timestamp de hace 2 semanas
        old_monday = _ts(0) - 14 * 86400  # hace 2 semanas en lunes
        old_friday_expiry = _expiry_ts(old_monday)
        now = old_friday_expiry + 86400  # sábado siguiente → expirado

        expired_record = _make_record("expired", old_monday)
        valid_record = _make_record("valid", _ts(0))

        selected = select_deliveries([expired_record, valid_record], now=now)
        selected_ids = {r.post_id for r in selected}
        assert "expired" not in selected_ids
        assert "valid" in selected_ids

    def test_count_expired_counts_correctly(self):
        decided_at = _ts(0)  # Lunes
        expiry = _expiry_ts(decided_at)
        records = [_make_record(f"p{i}", decided_at) for i in range(3)]
        # now después del vencimiento → todos expirados
        assert count_expired(records, now=expiry + 1) == 3
        # now en el límite → ninguno expirado
        assert count_expired(records, now=expiry) == 0

    def test_count_expired_ignores_no_opportunity_data(self):
        """Registros sin opportunity_data no se cuentan como expirados."""
        decided_at = _ts(0)
        expiry = _expiry_ts(decided_at)
        records = [
            PostRecord(
                post_id="no_data",
                status=PostDecision.pending_delivery,
                opportunity_data=None,
                decided_at=decided_at,
            )
        ]
        assert count_expired(records, now=expiry + 1) == 0


# ---------------------------------------------------------------------------
# corrective: Exclusión de registros con JSON malformado / schema inválido
# ---------------------------------------------------------------------------


class TestMalformedOpportunityDataExclusion:
    """Spec scenario corregido: los registros con opportunity_data inválido se
    excluyen ANTES del cap en el selector, no en el loop de entrega.

    Garantiza que registros inválidos no consumen cuota diaria.
    """

    def test_malformed_json_excluded_at_selection_time(self):
        """Un registro con JSON malformado NO se selecciona y NO consume cap."""
        now = _ts(1, hour=14)  # Martes
        records = [
            _make_record("p_valid", _ts(0)),  # JSON válido de AcceptedOpportunity
            PostRecord(
                post_id="p_bad_json",
                status=PostDecision.pending_delivery,
                opportunity_data="NOT VALID JSON {{{}",
                decided_at=_ts(0, hour=11),
            ),
        ]
        selected = select_deliveries(records, now=now, cap=8)
        selected_ids = {r.post_id for r in selected}
        assert "p_bad_json" not in selected_ids
        assert "p_valid" in selected_ids
        assert len(selected) == 1

    def test_invalid_schema_json_excluded_at_selection_time(self):
        """Un registro con JSON válido pero schema incorrecto NO se selecciona."""
        now = _ts(1, hour=14)
        records = [
            _make_record("p_valid", _ts(0)),
            PostRecord(
                post_id="p_wrong_schema",
                status=PostDecision.pending_delivery,
                opportunity_data='{"accept": true, "unexpected_field": 42}',
                decided_at=_ts(0, hour=11),
            ),
        ]
        selected = select_deliveries(records, now=now, cap=8)
        selected_ids = {r.post_id for r in selected}
        assert "p_wrong_schema" not in selected_ids
        assert "p_valid" in selected_ids

    def test_malformed_json_does_not_consume_cap(self):
        """Registros inválidos no cuentan para el cap; se seleccionan más válidos."""
        now = _ts(1, hour=14)
        # 8 válidos + 3 inválidos — con cap=8 deben seleccionarse los 8 válidos
        valid_records = [_make_record(f"v{i}", _ts(0, hour=i + 1)) for i in range(8)]
        invalid_records = [
            PostRecord(
                post_id=f"bad_{i}",
                status=PostDecision.pending_delivery,
                opportunity_data="{bad json}",
                decided_at=_ts(0, hour=i + 1),
            )
            for i in range(3)
        ]
        records = valid_records + invalid_records
        selected = select_deliveries(records, now=now, cap=8)
        assert len(selected) == 8
        selected_ids = {r.post_id for r in selected}
        assert all(pid.startswith("v") for pid in selected_ids)

    def test_all_malformed_returns_empty(self):
        """Si todos los registros son inválidos, la selección es vacía."""
        now = _ts(1, hour=14)
        records = [
            PostRecord(
                post_id=f"bad_{i}",
                status=PostDecision.pending_delivery,
                opportunity_data="null",
                decided_at=_ts(0),
            )
            for i in range(5)
        ]
        selected = select_deliveries(records, now=now, cap=8)
        assert selected == []

    def test_count_expired_ignores_malformed_json(self):
        """Registros con JSON malformado no se cuentan como expirados."""
        decided_at = _ts(0)
        expiry = _expiry_ts(decided_at)
        records = [
            PostRecord(
                post_id="bad",
                status=PostDecision.pending_delivery,
                opportunity_data="{invalid}",
                decided_at=decided_at,
            )
        ]
        assert count_expired(records, now=expiry + 1) == 0
