"""Renderizador determinístico de mensajes Telegram en HTML.

Sin efectos secundarios ni llamadas de red. Opera solo sobre datos persisted.
"""

from __future__ import annotations

import datetime
import html

from auto_reddit.shared.contracts import AcceptedOpportunity

# Mapa de tipos de oportunidad a etiquetas legibles en español
_OPPORTUNITY_TYPE_LABELS: dict[str, str] = {
    "funcionalidad": "Funcionalidad",
    "desarrollo": "Desarrollo",
    "dudas_si_merece_la_pena": "Dudas / ¿Merece la pena?",
    "comparativas": "Comparativas",
}


def _e(text: str | None) -> str:
    """Escapa texto para HTML de Telegram (caracteres especiales HTML)."""
    if text is None:
        return ""
    return html.escape(str(text))


def render_opportunity(opp: AcceptedOpportunity) -> str:
    """Genera el mensaje HTML para una oportunidad aceptada.

    Determinístico: mismo input → mismo output.
    Usa HTML parse mode de Telegram: <b>, <i>, <a href="...">, <blockquote>.
    """
    type_label = _OPPORTUNITY_TYPE_LABELS.get(
        opp.opportunity_type.value
        if hasattr(opp.opportunity_type, "value")
        else str(opp.opportunity_type),
        str(opp.opportunity_type),
    )

    lines: list[str] = []

    # Título y enlace
    lines.append(f'🔗 <b><a href="{_e(opp.link)}">{_e(opp.title)}</a></b>')
    lines.append("")

    # Tipo de oportunidad y razón
    lines.append(f"📌 <b>Tipo:</b> {_e(type_label)}")
    lines.append(f"💡 <b>Por qué:</b> {_e(opp.opportunity_reason)}")
    lines.append("")

    # Resumen del post
    lines.append(f"📄 <b>Resumen del post:</b>")
    lines.append(f"<blockquote>{_e(opp.post_summary_es)}</blockquote>")

    # Resumen de comentarios (opcional)
    if opp.comment_summary_es:
        lines.append(f"💬 <b>Resumen de comentarios:</b>")
        lines.append(f"<blockquote>{_e(opp.comment_summary_es)}</blockquote>")

    lines.append("")

    # Respuesta sugerida (ES)
    lines.append(f"✍️ <b>Respuesta sugerida (ES):</b>")
    lines.append(f"<blockquote>{_e(opp.suggested_response_es)}</blockquote>")

    # Respuesta sugerida (EN)
    lines.append(f"✍️ <b>Respuesta sugerida (EN):</b>")
    lines.append(f"<blockquote>{_e(opp.suggested_response_en)}</blockquote>")

    # Warning de contexto degradado (opcional)
    if opp.warning:
        lines.append("")
        lines.append(f"⚠️ <b>Aviso:</b> <i>{_e(opp.warning)}</i>")

    # Bullets de revisión humana (opcional)
    if opp.human_review_bullets:
        lines.append("")
        lines.append("🔎 <b>Puntos de revisión:</b>")
        for bullet in opp.human_review_bullets:
            lines.append(f"• {_e(bullet)}")

    return "\n".join(lines)


def render_summary(
    count: int,
    retry_count: int,
    new_count: int,
    *,
    date: datetime.date | None = None,
    reviewed_post_count: int | None = None,
) -> str:
    """Genera el mensaje HTML de resumen del envío diario.

    Conforme con ``docs/product/product.md §10``: el resumen inicial DEBE incluir
    fecha, número de oportunidades y número de posts revisados.

    Args:
        count: Total de oportunidades seleccionadas para entregar hoy.
        retry_count: Cuántas son reintentos de envíos anteriores.
        new_count: Cuántas son oportunidades nuevas.
        date: Fecha del ciclo de entrega (UTC). Si no se proporciona se usa
            la fecha actual UTC para mantener determinismo en producción.
        reviewed_post_count: Número de posts revisados en el ciclo de evaluación
            IA de hoy (pasado desde ``main.py``). Si no se proporciona se omite
            la línea (compatibilidad con llamadas internas sin ese contexto).

    Returns:
        Mensaje HTML de resumen.
    """
    if date is None:
        date = datetime.datetime.now(tz=datetime.timezone.utc).date()

    lines: list[str] = []
    lines.append("📬 <b>Resumen de oportunidades del día</b>")
    lines.append("")
    # Fecha — requerida por product.md §10
    lines.append(f"📅 Fecha: <b>{date.strftime('%d/%m/%Y')}</b>")
    # Posts revisados — requerido por product.md §10 cuando está disponible
    if reviewed_post_count is not None:
        lines.append(f"🔍 Posts revisados: <b>{reviewed_post_count}</b>")
    lines.append(f"📌 Oportunidades: <b>{count}</b>")
    if retry_count > 0:
        lines.append(f"  • Reintentos: <b>{retry_count}</b>")
    if new_count > 0:
        lines.append(f"  • Nuevas: <b>{new_count}</b>")
    lines.append("")
    lines.append("A continuación recibirás cada oportunidad por separado. 👇")
    return "\n".join(lines)
