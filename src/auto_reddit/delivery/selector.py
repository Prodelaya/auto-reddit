"""Selector determinístico de entregas Telegram.

Filtra registros expirados por TTL, prioriza reintentos y llena el cap con
oportunidades nuevas. Sin efectos secundarios; puro sobre la entrada.
"""

from __future__ import annotations

import datetime
import logging

from pydantic import ValidationError

from auto_reddit.shared.contracts import AcceptedOpportunity, PostDecision, PostRecord

logger = logging.getLogger(__name__)

# Sentinela de expiración: más allá de este timestamp (epoch) = expirado.
# Se calcula a partir de decided_at usando la regla de TTL semanal.


def _expiry_ts(decided_at: int) -> int:
    """Calcula el Unix timestamp del final del período de validez TTL.

    Regla:
    - Lunes (0), Martes (1), Miércoles (2) → vence el Viernes de esa semana a las 23:59:59 UTC
    - Jueves (3), Viernes (4)              → vence el Lunes siguiente a las 23:59:59 UTC
    - Sábado (5), Domingo (6)              → vence el Lunes siguiente a las 23:59:59 UTC (defensivo)
    """
    dt = datetime.datetime.fromtimestamp(decided_at, tz=datetime.timezone.utc)
    weekday = dt.weekday()  # 0=Mon … 6=Sun

    if weekday <= 2:
        # Lunes-Miércoles: avanzar hasta el viernes de la misma semana
        days_until_friday = 4 - weekday
        expiry_date = dt.date() + datetime.timedelta(days=days_until_friday)
    else:
        # Jueves-Domingo: avanzar hasta el lunes siguiente
        days_until_monday = 7 - weekday
        expiry_date = dt.date() + datetime.timedelta(days=days_until_monday)

    expiry_dt = datetime.datetime(
        expiry_date.year,
        expiry_date.month,
        expiry_date.day,
        23,
        59,
        59,
        tzinfo=datetime.timezone.utc,
    )
    return int(expiry_dt.timestamp())


def select_deliveries(
    records: list[PostRecord],
    now: int,
    cap: int = 8,
) -> list[PostRecord]:
    """Selecciona los registros a entregar hoy de forma determinística.

    Algoritmo:
    1. Filtra registros con ``opportunity_data`` None (no entregables).
    2. Separa los expirados (TTL < now) de los válidos.
    3. Ordena válidos: reintentos (tienen decided_at previo) vs. nuevos.
       Para este sistema todos los ``pending_delivery`` son candidatos;
       se considera "reintento" cualquier registro en ``pending_delivery``
       cuya primera inserción fue anterior al día actual — sin un campo
       explícito de intentos previos se usa ``decided_at ASC`` para priorizar
       los más antiguos (más tiempo esperando) como reintentos.
    4. Llena el cap: primero los reintentos más antiguos, luego los nuevos.

    Args:
        records: Todos los ``PostRecord`` en estado ``pending_delivery``.
        now: Timestamp Unix actual (inyectado para determinismo en tests).
        cap: Máximo de registros a entregar (por defecto 8).

    Returns:
        Lista ordenada [reintentos_más_antiguos…, nuevos_más_antiguos…],
        longitud ≤ cap.
    """
    # 1. Excluir registros sin opportunity_data o con JSON malformado / schema inválido.
    #    La validación ocurre aquí (antes del cap) para que los registros inválidos
    #    no consuman cuota de entrega ni lleguen al loop de envío.
    deliverable: list[PostRecord] = []
    for r in records:
        if r.opportunity_data is None:
            continue
        try:
            AcceptedOpportunity.model_validate_json(r.opportunity_data)
        except (ValidationError, ValueError) as exc:
            logger.debug("Invalid opportunity_data for %s: %s", r.post_id, exc)
            continue
        deliverable.append(r)

    # 2. Separar expirados de válidos
    valid: list[PostRecord] = []
    expired_count = 0
    for record in deliverable:
        if _expiry_ts(record.decided_at) >= now:
            valid.append(record)
        else:
            expired_count += 1

    # 3. Ordenar por decided_at ASC (más antiguos = más tiempo esperando = reintentos primero)
    valid.sort(key=lambda r: r.decided_at)

    # 4. Aplicar cap
    selected = valid[:cap]

    return selected


def count_expired(records: list[PostRecord], now: int) -> int:
    """Cuenta cuántos registros entregables válidos están expirados.

    Solo cuenta registros con ``opportunity_data`` no nulo y JSON schema válido.
    Utilizado por la fachada para poblar ``DeliveryReport.expired_skipped``.
    """
    deliverable: list[PostRecord] = []
    for r in records:
        if r.opportunity_data is None:
            continue
        try:
            AcceptedOpportunity.model_validate_json(r.opportunity_data)
        except (ValidationError, ValueError) as exc:
            logger.debug("Invalid opportunity_data for %s: %s", r.post_id, exc)
            continue
        deliverable.append(r)
    return sum(1 for r in deliverable if _expiry_ts(r.decided_at) < now)
