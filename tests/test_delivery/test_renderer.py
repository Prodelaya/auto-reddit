"""Tests para delivery/renderer.py.

Cubre:
- 4.2: render_opportunity() produce HTML válido de un AcceptedOpportunity fixture
- 4.2: render_opportunity() con y sin warning/bullets
- 4.2: render_opportunity() escapa caracteres HTML especiales
- 4.2: render_summary() formato de salida
- corrective: render_summary() incluye fecha y posts revisados (product.md §10)
"""

from __future__ import annotations

import datetime

import pytest

from auto_reddit.delivery.renderer import render_opportunity, render_summary
from auto_reddit.shared.contracts import AcceptedOpportunity, OpportunityType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_opportunity(
    *,
    warning: str | None = None,
    human_review_bullets: list[str] | None = None,
    comment_summary_es: str | None = "Nadie ha respondido todavía.",
) -> AcceptedOpportunity:
    return AcceptedOpportunity(
        post_id="abc123",
        title="How to configure Odoo Sales module?",
        link="https://www.reddit.com/r/Odoo/comments/abc123/",
        post_language="en",
        opportunity_type=OpportunityType.funcionalidad,
        opportunity_reason="El hilo está abierto y nadie ha explicado el paso de configuración.",
        post_summary_es="El usuario pregunta cómo configurar el módulo de ventas de Odoo.",
        comment_summary_es=comment_summary_es,
        suggested_response_es="Ve a Configuración > Ventas y activa la opción.",
        suggested_response_en="Go to Settings > Sales and enable the option.",
        warning=warning,
        human_review_bullets=human_review_bullets,
    )


# ---------------------------------------------------------------------------
# render_opportunity — salida básica
# ---------------------------------------------------------------------------


class TestRenderOpportunity:
    def test_contains_title(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "How to configure Odoo Sales module?" in html

    def test_contains_link(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "https://www.reddit.com/r/Odoo/comments/abc123/" in html

    def test_contains_opportunity_type_label(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "Funcionalidad" in html

    def test_contains_opportunity_reason(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "nadie ha explicado el paso de configuración" in html

    def test_contains_post_summary(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "módulo de ventas de Odoo" in html

    def test_contains_comment_summary_when_present(self):
        opp = _make_opportunity(comment_summary_es="Nadie ha respondido todavía.")
        html = render_opportunity(opp)
        assert "Nadie ha respondido todavía." in html

    def test_comment_summary_absent_when_none(self):
        opp = _make_opportunity(comment_summary_es=None)
        html = render_opportunity(opp)
        # No debe aparecer la sección de comentarios
        assert "Resumen de comentarios" not in html

    def test_contains_suggested_response_es(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "Ve a Configuración" in html

    def test_contains_suggested_response_en(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "Go to Settings" in html

    def test_uses_html_bold_tags(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "<b>" in html

    def test_uses_html_link_tag(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "<a href=" in html

    def test_uses_blockquote_tags(self):
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert "<blockquote>" in html

    def test_deterministic_same_input_same_output(self):
        opp = _make_opportunity()
        assert render_opportunity(opp) == render_opportunity(opp)


# ---------------------------------------------------------------------------
# render_opportunity — con warning y bullets (contexto degradado)
# ---------------------------------------------------------------------------


class TestRenderOpportunityDegradedContext:
    def test_contains_warning_when_present(self):
        opp = _make_opportunity(warning="Contexto degradado: solo top comments.")
        html = render_opportunity(opp)
        assert "Contexto degradado: solo top comments." in html
        assert "Aviso" in html

    def test_no_warning_section_when_absent(self):
        opp = _make_opportunity(warning=None)
        html = render_opportunity(opp)
        assert "Aviso" not in html

    def test_contains_bullets_when_present(self):
        bullets = ["Verificar si el hilo sigue activo.", "Confirmar relevancia."]
        opp = _make_opportunity(human_review_bullets=bullets)
        html = render_opportunity(opp)
        assert "Verificar si el hilo sigue activo." in html
        assert "Confirmar relevancia." in html
        assert "Puntos de revisión" in html

    def test_no_bullets_section_when_absent(self):
        opp = _make_opportunity(human_review_bullets=None)
        html = render_opportunity(opp)
        assert "Puntos de revisión" not in html

    def test_warning_uses_italic_tag(self):
        opp = _make_opportunity(warning="Aviso de contexto degradado.")
        html = render_opportunity(opp)
        assert "<i>" in html


# ---------------------------------------------------------------------------
# render_opportunity — escape de HTML
# ---------------------------------------------------------------------------


class TestRenderOpportunityHTMLEscape:
    def test_html_special_chars_in_title_are_escaped(self):
        opp = AcceptedOpportunity(
            post_id="xyz",
            title="Odoo <Sales> & Invoicing",
            link="https://example.com/",
            post_language="en",
            opportunity_type=OpportunityType.funcionalidad,
            opportunity_reason="Razón con <tags> & entidades.",
            post_summary_es='Resumen con "comillas" y <html>.',
            comment_summary_es=None,
            suggested_response_es="Respuesta con & símbolo.",
            suggested_response_en="Answer with & symbol.",
        )
        html = render_opportunity(opp)
        # Los caracteres < > & deben estar escapados en el texto
        assert "&lt;Sales&gt;" in html
        assert "&amp;" in html

    def test_link_url_not_escaped(self):
        """La URL del enlace debe estar intacta (no escapeada) en el atributo href."""
        opp = _make_opportunity()
        html = render_opportunity(opp)
        assert 'href="https://www.reddit.com/r/Odoo/comments/abc123/"' in html


# ---------------------------------------------------------------------------
# render_summary — formato de salida
# ---------------------------------------------------------------------------


class TestRenderSummary:
    def test_contains_total_count(self):
        html = render_summary(count=5, retry_count=2, new_count=3)
        assert "5" in html

    def test_contains_retry_count_when_present(self):
        html = render_summary(count=5, retry_count=2, new_count=3)
        assert "2" in html

    def test_contains_new_count_when_present(self):
        html = render_summary(count=5, retry_count=2, new_count=3)
        assert "3" in html

    def test_no_retry_line_when_zero_retries(self):
        html = render_summary(count=3, retry_count=0, new_count=3)
        assert "Reintentos" not in html

    def test_no_new_line_when_zero_new(self):
        html = render_summary(count=2, retry_count=2, new_count=0)
        assert "Nuevas" not in html

    def test_contains_html_bold_tags(self):
        html = render_summary(count=1, retry_count=0, new_count=1)
        assert "<b>" in html

    def test_deterministic_same_input_same_output(self):
        assert render_summary(3, 1, 2) == render_summary(3, 1, 2)

    def test_zero_count_summary(self):
        """render_summary con 0 oportunidades no debe lanzar error."""
        html = render_summary(count=0, retry_count=0, new_count=0)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_summary_has_header(self):
        html = render_summary(count=2, retry_count=1, new_count=1)
        assert "Resumen" in html


# ---------------------------------------------------------------------------
# corrective: render_summary incluye fecha y posts revisados (product.md §10)
# ---------------------------------------------------------------------------


class TestRenderSummaryProductAlignment:
    """Spec corregido: el resumen inicial de Telegram DEBE incluir fecha y número
    de posts revisados, según ``docs/product/product.md §10``.
    """

    def test_summary_includes_date_when_provided(self):
        """Si se pasa ``date``, el resumen incluye la fecha formateada."""
        fixed_date = datetime.date(2026, 3, 28)
        result = render_summary(count=3, retry_count=0, new_count=3, date=fixed_date)
        assert "28/03/2026" in result

    def test_summary_includes_reviewed_post_count_when_provided(self):
        """Si se pasa ``reviewed_post_count``, el resumen incluye el número."""
        result = render_summary(
            count=3, retry_count=0, new_count=3, reviewed_post_count=8
        )
        assert "8" in result
        assert "revisados" in result

    def test_summary_without_reviewed_post_count_omits_line(self):
        """Sin ``reviewed_post_count`` no aparece la línea de posts revisados."""
        result = render_summary(count=3, retry_count=0, new_count=3)
        assert "revisados" not in result

    def test_summary_date_defaults_to_today_utc(self):
        """Sin ``date`` explícita, la fecha es la de hoy en UTC."""
        today = datetime.datetime.now(tz=datetime.timezone.utc).date()
        result = render_summary(count=1, retry_count=0, new_count=1)
        assert today.strftime("%d/%m/%Y") in result

    def test_summary_deterministic_with_explicit_date(self):
        """render_summary es determinístico cuando se inyecta la fecha."""
        fixed = datetime.date(2026, 1, 15)
        r1 = render_summary(
            count=2, retry_count=1, new_count=1, date=fixed, reviewed_post_count=5
        )
        r2 = render_summary(
            count=2, retry_count=1, new_count=1, date=fixed, reviewed_post_count=5
        )
        assert r1 == r2

    def test_summary_includes_opportunity_count(self):
        """El número de oportunidades aparece en el resumen."""
        result = render_summary(
            count=5, retry_count=2, new_count=3, reviewed_post_count=8
        )
        assert "5" in result
