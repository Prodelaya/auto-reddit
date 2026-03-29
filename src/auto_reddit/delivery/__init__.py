"""Módulo de entrega de oportunidades por Telegram."""

from __future__ import annotations

import datetime
import logging

from auto_reddit.shared.contracts import AcceptedOpportunity, DeliveryReport

from .renderer import render_opportunity, render_summary
from .selector import count_expired, select_deliveries
from .telegram import send_message

logger = logging.getLogger(__name__)

_UTC = datetime.timezone.utc


def deliver_daily(
    store: "CandidateStore",  # type: ignore[name-defined]
    settings: "Settings",  # type: ignore[name-defined]
    *,
    reviewed_post_count: int | None = None,
    now_utc: datetime.datetime | None = None,
    run_date: datetime.date | None = None,
) -> DeliveryReport:
    """Ejecuta la entrega diaria de oportunidades aceptadas a Telegram.

    Flujo:
    1. Obtiene todos los ``pending_delivery`` del store.
    2. Selecciona el subconjunto a entregar hoy (retry-first, cap = max_daily_opportunities).
       Registros con ``opportunity_data`` None o JSON malformado son excluidos en el
       selector antes de consumir cuota del cap.
    3. Envía un mensaje de resumen (no bloqueante si falla), incluyendo fecha y número
       de posts revisados conforme a ``docs/product/product.md §10``.
    4. Por cada registro seleccionado:
       - Deserializa ``opportunity_data`` → ``AcceptedOpportunity``
       - Renderiza HTML
       - Envía a Telegram
       - Si éxito: ``store.mark_sent()``
       - Si fallo: logea y continúa (el registro permanece en pending_delivery)
    5. Devuelve ``DeliveryReport`` con las métricas del ciclo.

    Args:
        store: CandidateStore con acceso a la base de datos operativa.
        settings: Settings del proyecto (token, chat_id, cap).
        reviewed_post_count: Número de posts revisados en el ciclo IA actual.
            Pasado desde ``main.py`` para incluirlo en el resumen de Telegram.
            Si es None, la línea se omite del resumen.
        now_utc: Referencia temporal única (UTC) que gobierna TTL/selección,
            clasificación retry/new y fecha del resumen. Si es None se usa
            ``datetime.datetime.now(UTC)``. Inyectable para determinismo total.
        run_date: Alias de compatibilidad. Si se proporciona y ``now_utc`` es None,
            se construye ``now_utc`` como el inicio de ese día (00:00:00 UTC).
            Si se proporciona junto con ``now_utc``, ``now_utc`` tiene precedencia.

    Returns:
        DeliveryReport con totales de selección, envío y errores.
    """
    # --- Referencia temporal única ---
    if now_utc is None:
        if run_date is not None:
            now_utc = datetime.datetime(
                run_date.year, run_date.month, run_date.day, tzinfo=_UTC
            )
        else:
            now_utc = datetime.datetime.now(tz=_UTC)

    now_ts: int = int(now_utc.timestamp())
    today_date: datetime.date = now_utc.date()
    today_start_ts: int = int(
        now_utc.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )

    # 1. Obtener todos los pending_delivery
    all_pending = store.get_pending_deliveries()
    expired_count = count_expired(all_pending, now_ts)

    # 2. Seleccionar candidatos de hoy (retry-first, TTL-filtrado)
    selected = select_deliveries(
        all_pending, now_ts, cap=settings.max_daily_opportunities
    )
    total_selected = len(selected)

    # Calcular retries vs nuevas para el informe:
    # "reintento" = registros cuyo decided_at es anterior al inicio del día actual
    retry_count = sum(1 for r in selected if r.decided_at < today_start_ts)
    new_count = total_selected - retry_count

    # 3. Resumen (no bloqueante) — se emite SIEMPRE en cada ejecución de día laborable,
    #    incluso cuando no hay oportunidades seleccionadas (0-opportunity run).
    summary_html = render_summary(
        total_selected,
        retry_count,
        new_count,
        date=today_date,
        reviewed_post_count=reviewed_post_count,
    )
    summary_sent = send_message(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        summary_html,
    )
    if not summary_sent:
        logger.warning(
            "Resumen Telegram fallido — la entrega de oportunidades continúa"
        )

    # 4. Entregar oportunidades individuales
    sent_ok = 0
    sent_failed = 0

    for record in selected:
        if record.opportunity_data is None:
            logger.warning("Registro %s sin opportunity_data — saltado", record.post_id)
            sent_failed += 1
            continue

        try:
            opp = AcceptedOpportunity.model_validate_json(record.opportunity_data)
        except Exception as exc:
            logger.warning(
                "Error al deserializar opportunity_data de %s: %s",
                record.post_id,
                exc,
            )
            sent_failed += 1
            continue

        try:
            message_html = render_opportunity(opp)
        except Exception as exc:
            logger.warning(
                "Error al renderizar oportunidad %s: %s",
                record.post_id,
                exc,
            )
            sent_failed += 1
            continue

        success = send_message(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            message_html,
        )

        if success:
            store.mark_sent(record.post_id)
            sent_ok += 1
            logger.info("Entregado: %s", record.post_id)
        else:
            sent_failed += 1
            logger.warning(
                "Fallo de entrega Telegram para %s — permanece en pending_delivery",
                record.post_id,
            )

    return DeliveryReport(
        total_selected=total_selected,
        retries=retry_count,
        new=new_count,
        sent_ok=sent_ok,
        sent_failed=sent_failed,
        summary_sent=summary_sent,
        expired_skipped=expired_count,
    )


__all__ = ["deliver_daily"]
