"""Tests para los contratos Pydantic de evaluación IA (Change 4).

Cubre:
- 4.1a: AIRawResponse acepta JSON de aceptación válido
- 4.1b: AIRawResponse acepta JSON de rechazo válido
- 4.1c: AIRawResponse rechaza campos faltantes obligatorios
- 4.1d: AIRawResponse rechaza valores de enum inválidos
- 4.1e: AcceptedOpportunity.model_dump_json() round-trip limpio
- 4.1f: AcceptedOpportunity con degraded context incluye warning + bullets
- 4.1g: RejectedPost valida correctamente
- 4.1h: EvaluationResult acepta AcceptedOpportunity y RejectedPost
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from auto_reddit.shared.contracts import (
    AIRawResponse,
    AcceptedOpportunity,
    EvaluationResult,
    OpportunityType,
    RejectedPost,
    RejectionType,
)


# ---------------------------------------------------------------------------
# 4.1a — AIRawResponse acepta JSON de aceptación válido
# ---------------------------------------------------------------------------


class TestAIRawResponseAccepted:
    def test_valid_accepted_response_parses_correctly(self):
        data = {
            "accept": True,
            "opportunity_type": "funcionalidad",
            "opportunity_reason": "El hilo está abierto y nadie ha explicado el paso de configuración.",
            "post_language": "en",
            "post_summary_es": "El usuario pregunta cómo configurar el módulo de ventas.",
            "comment_summary_es": "Nadie ha respondido todavía.",
            "suggested_response_es": "Puedes ir a Configuración > Ventas y activar la opción.",
            "suggested_response_en": "Go to Settings > Sales and enable the option.",
        }
        response = AIRawResponse.model_validate(data)
        assert response.accept is True
        assert response.opportunity_type == OpportunityType.funcionalidad
        assert (
            response.opportunity_reason
            == "El hilo está abierto y nadie ha explicado el paso de configuración."
        )
        assert response.post_language == "en"
        assert (
            response.post_summary_es
            == "El usuario pregunta cómo configurar el módulo de ventas."
        )
        assert response.rejection_type is None
        assert response.warning is None
        assert response.human_review_bullets is None

    def test_accepted_without_opportunity_reason_is_valid(self):
        """opportunity_reason is optional in AIRawResponse (None by default)."""
        data = {
            "accept": True,
            "opportunity_type": "funcionalidad",
            "post_language": "en",
            "post_summary_es": "Resumen",
            "comment_summary_es": "Comentarios",
            "suggested_response_es": "Respuesta",
            "suggested_response_en": "Response",
        }
        response = AIRawResponse.model_validate(data)
        assert response.opportunity_reason is None

    def test_accepted_with_null_comment_summary_is_valid(self):
        """comment_summary_es can be None/null when there are no useful comments."""
        data = {
            "accept": True,
            "opportunity_type": "desarrollo",
            "opportunity_reason": "Pregunta técnica sin respuesta.",
            "post_language": "es",
            "post_summary_es": "Pregunta técnica.",
            "comment_summary_es": None,
            "suggested_response_es": "Respuesta técnica.",
            "suggested_response_en": "Technical answer.",
        }
        response = AIRawResponse.model_validate(data)
        assert response.comment_summary_es is None

    def test_all_opportunity_types_are_valid(self):
        for opp_type in OpportunityType:
            data = {
                "accept": True,
                "opportunity_type": opp_type.value,
                "opportunity_reason": "Razón de oportunidad.",
                "post_language": "es",
                "post_summary_es": "Resumen",
                "comment_summary_es": "Comentarios",
                "suggested_response_es": "Respuesta es",
                "suggested_response_en": "Response en",
            }
            response = AIRawResponse.model_validate(data)
            assert response.opportunity_type == opp_type


# ---------------------------------------------------------------------------
# 4.1b — AIRawResponse acepta JSON de rechazo válido
# ---------------------------------------------------------------------------


class TestAIRawResponseRejected:
    def test_valid_rejected_response_parses_correctly(self):
        data = {
            "accept": False,
            "rejection_type": "resolved_or_closed",
        }
        response = AIRawResponse.model_validate(data)
        assert response.accept is False
        assert response.rejection_type == RejectionType.resolved_or_closed
        assert response.opportunity_type is None

    def test_all_rejection_types_are_valid(self):
        for rej_type in RejectionType:
            data = {"accept": False, "rejection_type": rej_type.value}
            response = AIRawResponse.model_validate(data)
            assert response.rejection_type == rej_type


# ---------------------------------------------------------------------------
# 4.1c — AIRawResponse rechaza campos faltantes obligatorios
# ---------------------------------------------------------------------------


class TestAIRawResponseMissingFields:
    def test_missing_accept_field_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            AIRawResponse.model_validate({"opportunity_type": "funcionalidad"})
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("accept",) for e in errors)

    def test_empty_dict_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AIRawResponse.model_validate({})


# ---------------------------------------------------------------------------
# 4.1d — AIRawResponse rechaza valores de enum inválidos
# ---------------------------------------------------------------------------


class TestAIRawResponseInvalidEnums:
    def test_invalid_opportunity_type_raises_validation_error(self):
        data = {
            "accept": True,
            "opportunity_type": "inexistente",
            "post_language": "es",
            "post_summary_es": "Resumen",
            "comment_summary_es": "Comentarios",
            "suggested_response_es": "Respuesta",
            "suggested_response_en": "Response",
        }
        with pytest.raises(ValidationError) as exc_info:
            AIRawResponse.model_validate(data)
        errors = exc_info.value.errors()
        assert any("opportunity_type" in str(e["loc"]) for e in errors)

    def test_invalid_rejection_type_raises_validation_error(self):
        data = {"accept": False, "rejection_type": "not_a_valid_type"}
        with pytest.raises(ValidationError) as exc_info:
            AIRawResponse.model_validate(data)
        errors = exc_info.value.errors()
        assert any("rejection_type" in str(e["loc"]) for e in errors)


# ---------------------------------------------------------------------------
# 4.1e — AcceptedOpportunity.model_dump_json() round-trip limpio
# ---------------------------------------------------------------------------


class TestAcceptedOpportunityRoundTrip:
    def _make_accepted(self) -> AcceptedOpportunity:
        return AcceptedOpportunity(
            post_id="abc123",
            title="How to configure Odoo Sales module?",
            link="https://www.reddit.com/r/Odoo/comments/abc123/",
            post_language="en",
            opportunity_type=OpportunityType.funcionalidad,
            opportunity_reason="El hilo está abierto y no hay respuesta que explique la configuración.",
            post_summary_es="Pregunta sobre configuración del módulo de ventas.",
            comment_summary_es="Sin respuestas útiles aún.",
            suggested_response_es="Ve a Configuración > Ventas.",
            suggested_response_en="Go to Settings > Sales.",
        )

    def test_model_dump_json_produces_valid_json(self):
        opp = self._make_accepted()
        json_str = opp.model_dump_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_model_dump_json_contains_required_fields(self):
        opp = self._make_accepted()
        parsed = json.loads(opp.model_dump_json())
        assert parsed["post_id"] == "abc123"
        assert parsed["title"] == "How to configure Odoo Sales module?"
        assert parsed["link"] == "https://www.reddit.com/r/Odoo/comments/abc123/"
        assert parsed["post_language"] == "en"
        assert parsed["opportunity_type"] == "funcionalidad"
        assert (
            parsed["opportunity_reason"]
            == "El hilo está abierto y no hay respuesta que explique la configuración."
        )
        assert (
            parsed["post_summary_es"]
            == "Pregunta sobre configuración del módulo de ventas."
        )
        assert parsed["suggested_response_es"] == "Ve a Configuración > Ventas."
        assert parsed["suggested_response_en"] == "Go to Settings > Sales."

    def test_roundtrip_model_validates_from_json(self):
        opp = self._make_accepted()
        json_str = opp.model_dump_json()
        opp2 = AcceptedOpportunity.model_validate_json(json_str)
        assert opp2.post_id == opp.post_id
        assert opp2.opportunity_type == opp.opportunity_type
        assert opp2.opportunity_reason == opp.opportunity_reason

    def test_opportunity_type_serialized_as_string_value(self):
        opp = self._make_accepted()
        parsed = json.loads(opp.model_dump_json())
        assert parsed["opportunity_type"] == "funcionalidad"  # enum value, not name

    def test_null_optional_fields_when_no_degraded_context(self):
        opp = self._make_accepted()
        parsed = json.loads(opp.model_dump_json())
        assert parsed["warning"] is None
        assert parsed["human_review_bullets"] is None

    def test_comment_summary_es_can_be_null(self):
        """comment_summary_es is optional — None when no useful comments."""
        opp = AcceptedOpportunity(
            post_id="abc456",
            title="Silent post",
            link="https://www.reddit.com/r/Odoo/comments/abc456/",
            post_language="en",
            opportunity_type=OpportunityType.desarrollo,
            opportunity_reason="Pregunta técnica sin respuestas.",
            post_summary_es="El post pregunta algo técnico.",
            comment_summary_es=None,
            suggested_response_es="Respuesta técnica.",
            suggested_response_en="Technical answer.",
        )
        parsed = json.loads(opp.model_dump_json())
        assert parsed["comment_summary_es"] is None


# ---------------------------------------------------------------------------
# 4.1f — AcceptedOpportunity con degraded context incluye warning + bullets
# ---------------------------------------------------------------------------


class TestAcceptedOpportunityDegradedContext:
    def test_degraded_context_fields_preserved(self):
        opp = AcceptedOpportunity(
            post_id="xyz789",
            title="Odoo vs SAP — worth it?",
            link="https://www.reddit.com/r/Odoo/comments/xyz789/",
            post_language="en",
            opportunity_type=OpportunityType.comparativas,
            opportunity_reason="El hilo busca comparativa activa y podemos aportar contexto real.",
            post_summary_es="Comparativa entre Odoo y SAP.",
            comment_summary_es="Varios comentarios pero contexto incompleto.",
            suggested_response_es="Depende del caso de uso...",
            suggested_response_en="It depends on the use case...",
            warning="Contexto degradado: solo top comments, sin timestamps.",
            human_review_bullets=[
                "Verificar si el hilo sigue activo.",
                "Confirmar que la comparativa es relevante para el contexto del equipo.",
            ],
        )
        json_str = opp.model_dump_json()
        parsed = json.loads(json_str)
        assert (
            parsed["warning"]
            == "Contexto degradado: solo top comments, sin timestamps."
        )
        assert len(parsed["human_review_bullets"]) == 2
        assert (
            parsed["opportunity_reason"]
            == "El hilo busca comparativa activa y podemos aportar contexto real."
        )


# ---------------------------------------------------------------------------
# 4.1g — RejectedPost valida correctamente
# ---------------------------------------------------------------------------


class TestRejectedPostContract:
    def test_valid_rejected_post(self):
        rp = RejectedPost(
            post_id="post_001", rejection_type=RejectionType.no_useful_contribution
        )
        assert rp.post_id == "post_001"
        assert rp.rejection_type == RejectionType.no_useful_contribution

    def test_rejected_post_all_rejection_types(self):
        for rej_type in RejectionType:
            rp = RejectedPost(post_id="p", rejection_type=rej_type)
            assert rp.rejection_type == rej_type

    def test_rejected_post_missing_rejection_type_raises(self):
        with pytest.raises(ValidationError):
            RejectedPost(post_id="p")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# 4.1h — EvaluationResult acepta AcceptedOpportunity y RejectedPost
# ---------------------------------------------------------------------------


class TestEvaluationResultUnion:
    def test_accepted_is_valid_evaluation_result(self):
        opp = AcceptedOpportunity(
            post_id="a",
            title="T",
            link="https://example.com",
            post_language="en",
            opportunity_type=OpportunityType.desarrollo,
            opportunity_reason="Pregunta técnica sin respuesta.",
            post_summary_es="Resumen",
            comment_summary_es="Comentarios",
            suggested_response_es="Respuesta",
            suggested_response_en="Response",
        )
        # EvaluationResult is a type alias (Union); isinstance checks work on concrete types
        assert isinstance(opp, AcceptedOpportunity)

    def test_rejected_is_valid_evaluation_result(self):
        rp = RejectedPost(post_id="b", rejection_type=RejectionType.excluded_topic)
        assert isinstance(rp, RejectedPost)

    def test_evaluation_result_list_holds_mixed_types(self):
        results: list[EvaluationResult] = [
            AcceptedOpportunity(
                post_id="c",
                title="T",
                link="https://example.com",
                post_language="es",
                opportunity_type=OpportunityType.dudas_si_merece_la_pena,
                opportunity_reason="Aportación útil posible.",
                post_summary_es="Resumen",
                comment_summary_es=None,
                suggested_response_es="Respuesta",
                suggested_response_en="Response",
            ),
            RejectedPost(post_id="d", rejection_type=RejectionType.resolved_or_closed),
        ]
        assert len(results) == 2
        assert isinstance(results[0], AcceptedOpportunity)
        assert isinstance(results[1], RejectedPost)
