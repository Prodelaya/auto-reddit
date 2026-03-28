"""Tests para evaluation/evaluator.py (Change 4).

Cubre:
- 4.2a: respuesta aceptada válida → AcceptedOpportunity
- 4.2b: respuesta rechazada válida → RejectedPost
- 4.2c: contexto degradado → warning + human_review_bullets presentes en resultado
- 4.2d: JSON inválido → skip (None)
- 4.2e: APIError persistente tras retries → skip (None)
- 4.3:  evaluate_batch con lista vacía → lista vacía, sin llamadas API
- 4.4:  evaluate_batch con 1 aceptado, 1 rechazado, 1 fallo → 2 resultados, 1 saltado
- 4.5:  integración en main: mocked evaluate_batch → save_pending_delivery / save_rejected
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import pytest
from openai import APIError

from auto_reddit.evaluation.evaluator import (
    _build_system_prompt,
    _build_user_message,
    _evaluate_single,
    evaluate_batch,
)
from auto_reddit.shared.contracts import (
    AcceptedOpportunity,
    ContextQuality,
    OpportunityType,
    RedditCandidate,
    RedditComment,
    RejectedPost,
    RejectionType,
    ThreadContext,
)


# ---------------------------------------------------------------------------
# Helpers — factories
# ---------------------------------------------------------------------------


def _make_candidate(post_id: str = "post_001") -> RedditCandidate:
    return RedditCandidate(
        post_id=post_id,
        title="How do I configure Odoo Sales module?",
        selftext="I'm trying to set up the sales module in Odoo 17. Any tips?",
        url=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        permalink=f"https://www.reddit.com/r/Odoo/comments/{post_id}/test/",
        author="testuser",
        subreddit="Odoo",
        created_utc=1_700_000_000,
        source_api="reddit3",
    )


def _make_comment(body: str = "Have you tried going to Settings?") -> RedditComment:
    return RedditComment(
        comment_id="c_001",
        author="helper_user",
        body=body,
        score=5,
        source_api="reddit3",
    )


def _make_thread_context(
    post_id: str = "post_001",
    quality: ContextQuality = ContextQuality.full,
    comments: list[RedditComment] | None = None,
) -> ThreadContext:
    return ThreadContext(
        candidate=_make_candidate(post_id),
        comments=comments or [_make_comment()],
        comment_count=1,
        quality=quality,
        source_api="reddit3",
    )


def _make_settings() -> MagicMock:
    settings = MagicMock()
    settings.deepseek_api_key = "test-key"
    settings.deepseek_model = "deepseek-chat"
    return settings


def _make_openai_response(content: dict) -> MagicMock:
    """Construye un MagicMock que simula la respuesta de OpenAI."""
    message = MagicMock()
    message.content = json.dumps(content)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# 4.2a — Respuesta aceptada válida → AcceptedOpportunity
# ---------------------------------------------------------------------------


class TestEvaluateSingleAccepted:
    def test_valid_accepted_response_returns_accepted_opportunity(self):
        ctx = _make_thread_context()
        client = MagicMock()
        accepted_json = {
            "accept": True,
            "opportunity_type": "funcionalidad",
            "opportunity_reason": "El hilo está abierto y podemos guiar la configuración.",
            "post_language": "en",
            "post_summary_es": "Pregunta sobre configuración de ventas.",
            "comment_summary_es": "Un usuario sugirió ir a Settings.",
            "suggested_response_es": "Ve a Configuración > Ventas y activa la opción.",
            "suggested_response_en": "Go to Settings > Sales and enable the option.",
        }
        client.chat.completions.create.return_value = _make_openai_response(
            accepted_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, AcceptedOpportunity)
        assert result.post_id == "post_001"
        assert result.title == "How do I configure Odoo Sales module?"
        assert result.link == "https://www.reddit.com/r/Odoo/comments/post_001/"
        assert result.post_language == "en"
        assert result.opportunity_type == OpportunityType.funcionalidad
        assert (
            result.opportunity_reason
            == "El hilo está abierto y podemos guiar la configuración."
        )
        assert result.post_summary_es == "Pregunta sobre configuración de ventas."
        assert result.warning is None
        assert result.human_review_bullets is None

    def test_accepted_with_null_comment_summary(self):
        """comment_summary_es can be null when no useful comments exist."""
        ctx = _make_thread_context(comments=[])
        ctx = ThreadContext(
            candidate=_make_candidate(),
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit3",
        )
        client = MagicMock()
        accepted_json = {
            "accept": True,
            "opportunity_type": "desarrollo",
            "opportunity_reason": "Pregunta técnica abierta sin respuestas.",
            "post_language": "en",
            "post_summary_es": "Pregunta técnica de Python.",
            "comment_summary_es": None,
            "suggested_response_es": "Puedes usar un computed field.",
            "suggested_response_en": "You can use a computed field.",
        }
        client.chat.completions.create.return_value = _make_openai_response(
            accepted_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, AcceptedOpportunity)
        assert result.comment_summary_es is None

    def test_accepted_fields_are_set_from_ai_response(self):
        ctx = _make_thread_context()
        client = MagicMock()
        accepted_json = {
            "accept": True,
            "opportunity_type": "desarrollo",
            "opportunity_reason": "Pregunta técnica Python sin respuesta experta.",
            "post_language": "es",
            "post_summary_es": "Pregunta técnica de Python.",
            "comment_summary_es": "Sin respuesta aún.",
            "suggested_response_es": "Puedes usar un computed field.",
            "suggested_response_en": "You can use a computed field.",
        }
        client.chat.completions.create.return_value = _make_openai_response(
            accepted_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, AcceptedOpportunity)
        assert result.opportunity_type == OpportunityType.desarrollo
        assert result.post_language == "es"


# ---------------------------------------------------------------------------
# 4.2b — Respuesta rechazada válida → RejectedPost
# ---------------------------------------------------------------------------


class TestEvaluateSingleRejected:
    def test_valid_rejected_response_returns_rejected_post(self):
        ctx = _make_thread_context()
        client = MagicMock()
        rejected_json = {"accept": False, "rejection_type": "resolved_or_closed"}
        client.chat.completions.create.return_value = _make_openai_response(
            rejected_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, RejectedPost)
        assert result.post_id == "post_001"
        assert result.rejection_type == RejectionType.resolved_or_closed

    def test_all_rejection_types_produce_rejected_post(self):
        ctx = _make_thread_context()
        client = MagicMock()
        for rej_type in RejectionType:
            client.chat.completions.create.return_value = _make_openai_response(
                {"accept": False, "rejection_type": rej_type.value}
            )
            result = _evaluate_single(ctx, client, "deepseek-chat")
            assert isinstance(result, RejectedPost)
            assert result.rejection_type == rej_type


# ---------------------------------------------------------------------------
# 4.2c — Contexto degradado → warning + human_review_bullets en AcceptedOpportunity
# ---------------------------------------------------------------------------


class TestEvaluateSingleDegradedContext:
    def test_degraded_context_accepted_includes_warning_and_bullets(self):
        ctx = _make_thread_context(quality=ContextQuality.degraded)
        client = MagicMock()
        accepted_json = {
            "accept": True,
            "opportunity_type": "comparativas",
            "opportunity_reason": "El hilo busca comparativa activa y podemos aportar perspectiva.",
            "post_language": "en",
            "post_summary_es": "Comparativa Odoo vs SAP.",
            "comment_summary_es": "Comentarios incompletos.",
            "suggested_response_es": "Depende del caso de uso.",
            "suggested_response_en": "It depends on the use case.",
            "warning": "Contexto degradado: top comments únicamente, sin timestamps.",
            "human_review_bullets": [
                "Verificar si el hilo sigue activo.",
                "Confirmar relevancia de la comparativa.",
            ],
        }
        client.chat.completions.create.return_value = _make_openai_response(
            accepted_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, AcceptedOpportunity)
        assert result.warning is not None
        assert (
            "degradado" in result.warning.lower()
            or "degraded" in result.warning.lower()
            or result.warning
        )
        assert result.human_review_bullets is not None
        assert len(result.human_review_bullets) == 2
        assert (
            result.opportunity_reason
            == "El hilo busca comparativa activa y podemos aportar perspectiva."
        )

    def test_degraded_context_rejected_has_no_warning_or_bullets(self):
        """Rejected posts NEVER carry warning/bullets — those are accepted-only fields.

        Even if the AI model includes warning/human_review_bullets in its JSON response
        for a rejected post, the pipeline maps the result to RejectedPost which has no
        such fields, so they are silently dropped by design.
        """
        ctx = _make_thread_context(quality=ContextQuality.degraded)
        client = MagicMock()
        # Even if the AI (incorrectly) includes warning in a rejected response,
        # the pipeline must NOT expose those fields on RejectedPost.
        rejected_json = {
            "accept": False,
            "rejection_type": "insufficient_evidence",
            "warning": "Contexto degradado.",
            "human_review_bullets": ["Revisar cuando haya más contexto."],
        }
        client.chat.completions.create.return_value = _make_openai_response(
            rejected_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, RejectedPost)
        assert result.rejection_type == RejectionType.insufficient_evidence
        # RejectedPost has no warning/bullets fields — authoritative rule
        assert not hasattr(result, "warning")
        assert not hasattr(result, "human_review_bullets")


# ---------------------------------------------------------------------------
# Spec scenario: partial context → normal evaluation, no degraded cues
# ---------------------------------------------------------------------------


class TestEvaluateSinglePartialContext:
    """Spec: 'Evaluate partial context without extra gating.'

    When quality=partial, the post is evaluated normally.
    No warning or human_review_bullets are required (or expected).
    """

    def test_partial_context_accepted_has_no_warning_no_bullets(self):
        """Accepted result for partial context must not carry degraded review cues."""
        ctx = _make_thread_context(quality=ContextQuality.partial)
        client = MagicMock()
        accepted_json = {
            "accept": True,
            "opportunity_type": "funcionalidad",
            "opportunity_reason": "Pregunta abierta con aportación técnica útil.",
            "post_language": "en",
            "post_summary_es": "Pregunta sobre configuración de ventas.",
            "comment_summary_es": "Un usuario sugirió ir a Settings.",
            "suggested_response_es": "Ve a Configuración > Ventas.",
            "suggested_response_en": "Go to Settings > Sales.",
        }
        client.chat.completions.create.return_value = _make_openai_response(
            accepted_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, AcceptedOpportunity)
        assert result.post_id == "post_001"
        # partial context: no degraded cues required
        assert result.warning is None
        assert result.human_review_bullets is None

    def test_partial_context_rejected_returns_clean_rejected_post(self):
        """Rejected result for partial context: just post_id + rejection_type."""
        ctx = _make_thread_context(quality=ContextQuality.partial)
        client = MagicMock()
        rejected_json = {"accept": False, "rejection_type": "resolved_or_closed"}
        client.chat.completions.create.return_value = _make_openai_response(
            rejected_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert isinstance(result, RejectedPost)
        assert result.post_id == "post_001"
        assert result.rejection_type == RejectionType.resolved_or_closed

    def test_partial_context_user_message_has_no_aviso(self):
        """User message for partial context must NOT include the degraded-context aviso."""
        ctx = _make_thread_context(quality=ContextQuality.partial)
        msg = _build_user_message(ctx)
        assert "degradado" not in msg.lower()
        assert "AVISO DE CONTEXTO" not in msg
        # quality indicator is still present (for full transparency to the model)
        assert "partial" in msg


# ---------------------------------------------------------------------------
# 4.2d — JSON inválido → skip (None)
# ---------------------------------------------------------------------------


class TestEvaluateSingleInvalidJSON:
    def test_invalid_json_returns_none(self):
        ctx = _make_thread_context()
        client = MagicMock()
        # Simulate content that is not valid JSON
        message = MagicMock()
        message.content = "Este no es JSON válido {{{{invalid"
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        client.chat.completions.create.return_value = response

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert result is None

    def test_empty_content_returns_none(self):
        ctx = _make_thread_context()
        client = MagicMock()
        message = MagicMock()
        message.content = ""
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        client.chat.completions.create.return_value = response

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert result is None

    def test_json_with_invalid_enum_returns_none(self):
        ctx = _make_thread_context()
        client = MagicMock()
        # Valid JSON but invalid enum value → ValidationError → skip
        invalid_json = {"accept": False, "rejection_type": "valor_inventado"}
        client.chat.completions.create.return_value = _make_openai_response(
            invalid_json
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert result is None


# ---------------------------------------------------------------------------
# 4.2e — APIError persistente tras retries → skip (None)
# ---------------------------------------------------------------------------


class TestEvaluateSingleAPIError:
    def test_persistent_api_error_returns_none(self):
        ctx = _make_thread_context()
        client = MagicMock()
        # Simula fallo en cada intento
        client.chat.completions.create.side_effect = APIError(
            message="Rate limit exceeded",
            request=MagicMock(),
            body=None,
        )

        result = _evaluate_single(ctx, client, "deepseek-chat")

        assert result is None
        # Tenacity retries 3 times
        assert client.chat.completions.create.call_count == 3


# ---------------------------------------------------------------------------
# 4.3 — evaluate_batch con lista vacía → lista vacía, sin llamadas API
# ---------------------------------------------------------------------------


class TestEvaluateBatchEmptyInput:
    def test_empty_input_returns_empty_list(self):
        settings = _make_settings()
        with patch("auto_reddit.evaluation.evaluator.OpenAI") as mock_openai_cls:
            result = evaluate_batch([], settings)

        assert result == []
        # No OpenAI client should be created for empty input
        # (evaluate_batch returns early before creating client)
        mock_openai_cls.assert_not_called()

    def test_empty_input_no_api_calls(self):
        settings = _make_settings()
        with patch("auto_reddit.evaluation.evaluator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            result = evaluate_batch([], settings)

        assert result == []
        mock_client.chat.completions.create.assert_not_called()


# ---------------------------------------------------------------------------
# 4.4 — evaluate_batch con 1 aceptado, 1 rechazado, 1 fallo → 2 resultados, 1 saltado
# ---------------------------------------------------------------------------


class TestEvaluateBatchMixedResults:
    def test_batch_with_accept_reject_failure_returns_two_results(self):
        ctx_accept = _make_thread_context(post_id="post_accept")
        ctx_reject = _make_thread_context(post_id="post_reject")
        ctx_fail = _make_thread_context(post_id="post_fail")

        settings = _make_settings()

        accepted_json = {
            "accept": True,
            "opportunity_type": "funcionalidad",
            "opportunity_reason": "Pregunta abierta sin respuesta experta.",
            "post_language": "en",
            "post_summary_es": "Resumen.",
            "comment_summary_es": "Sin comentarios.",
            "suggested_response_es": "Respuesta.",
            "suggested_response_en": "Response.",
        }
        rejected_json = {"accept": False, "rejection_type": "no_useful_contribution"}

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_openai_response(accepted_json)
            elif call_count == 2:
                return _make_openai_response(rejected_json)
            else:
                raise APIError(message="Server error", request=MagicMock(), body=None)

        with patch("auto_reddit.evaluation.evaluator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = side_effect
            mock_openai_cls.return_value = mock_client

            results = evaluate_batch([ctx_accept, ctx_reject, ctx_fail], settings)

        assert len(results) == 2
        assert isinstance(results[0], AcceptedOpportunity)
        assert results[0].post_id == "post_accept"
        assert isinstance(results[1], RejectedPost)
        assert results[1].post_id == "post_reject"
        # post_fail was skipped (API error after 3 retries)
        result_ids = {r.post_id for r in results}
        assert "post_fail" not in result_ids

    def test_all_failed_returns_empty_list(self):
        contexts = [_make_thread_context(post_id=f"post_{i}") for i in range(3)]
        settings = _make_settings()

        with patch("auto_reddit.evaluation.evaluator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = APIError(
                message="Down", request=MagicMock(), body=None
            )
            mock_openai_cls.return_value = mock_client

            results = evaluate_batch(contexts, settings)

        assert results == []


# ---------------------------------------------------------------------------
# 4.5 — Integración en main: mocked evaluate_batch → save_pending_delivery / save_rejected
# ---------------------------------------------------------------------------


class TestMainIntegration:
    """Verifica que main.run() llama save_pending_delivery / save_rejected según el resultado."""

    def _make_accepted_opportunity(
        self, post_id: str = "post_accepted"
    ) -> AcceptedOpportunity:
        return AcceptedOpportunity(
            post_id=post_id,
            title="Test post",
            link=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
            post_language="en",
            opportunity_type=OpportunityType.funcionalidad,
            opportunity_reason="Pregunta abierta con aportación técnica posible.",
            post_summary_es="Resumen.",
            comment_summary_es="Sin comentarios.",
            suggested_response_es="Respuesta.",
            suggested_response_en="Response.",
        )

    def _make_rejected_post(self, post_id: str = "post_rejected") -> RejectedPost:
        return RejectedPost(
            post_id=post_id, rejection_type=RejectionType.resolved_or_closed
        )

    def test_accepted_triggers_save_pending_delivery(self):
        import datetime as _datetime

        accepted = self._make_accepted_opportunity("post_a")
        mock_store = MagicMock()

        mock_store.get_decided_post_ids.return_value = set()

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.collect_candidates") as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts") as mock_fetch,
            patch("auto_reddit.main.evaluate_batch") as mock_eval,
            patch("auto_reddit.main.CandidateStore") as mock_store_cls,
            patch("auto_reddit.main.settings") as mock_settings,
            patch("auto_reddit.main.deliver_daily"),
        ):
            # Force weekday (Wednesday) to bypass weekend guard
            mock_dt.date.today.return_value = _datetime.date(2026, 3, 25)
            mock_settings.db_path = ":memory:"
            mock_settings.daily_review_limit = 8
            mock_settings.deepseek_model = "deepseek-chat"
            mock_store_cls.return_value = mock_store
            mock_collect.return_value = []
            mock_fetch.return_value = []
            mock_eval.return_value = [accepted]

            from auto_reddit.main import run

            run()

        mock_store.save_pending_delivery.assert_called_once_with(
            "post_a", accepted.model_dump_json()
        )
        mock_store.save_rejected.assert_not_called()

    def test_rejected_triggers_save_rejected(self):
        import datetime as _datetime

        rejected = self._make_rejected_post("post_b")
        mock_store = MagicMock()
        mock_store.get_decided_post_ids.return_value = set()

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.collect_candidates") as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts") as mock_fetch,
            patch("auto_reddit.main.evaluate_batch") as mock_eval,
            patch("auto_reddit.main.CandidateStore") as mock_store_cls,
            patch("auto_reddit.main.settings") as mock_settings,
            patch("auto_reddit.main.deliver_daily"),
        ):
            # Force weekday (Wednesday) to bypass weekend guard
            mock_dt.date.today.return_value = _datetime.date(2026, 3, 25)
            mock_settings.db_path = ":memory:"
            mock_settings.daily_review_limit = 8
            mock_settings.deepseek_model = "deepseek-chat"
            mock_store_cls.return_value = mock_store
            mock_collect.return_value = []
            mock_fetch.return_value = []
            mock_eval.return_value = [rejected]

            from auto_reddit.main import run

            run()

        mock_store.save_rejected.assert_called_once_with("post_b")
        mock_store.save_pending_delivery.assert_not_called()

    def test_mixed_batch_calls_correct_persistence_methods(self):
        import datetime as _datetime

        accepted = self._make_accepted_opportunity("post_a")
        rejected = self._make_rejected_post("post_b")
        mock_store = MagicMock()
        mock_store.get_decided_post_ids.return_value = set()

        with (
            patch("auto_reddit.main.datetime") as mock_dt,
            patch("auto_reddit.main.collect_candidates") as mock_collect,
            patch("auto_reddit.main.fetch_thread_contexts") as mock_fetch,
            patch("auto_reddit.main.evaluate_batch") as mock_eval,
            patch("auto_reddit.main.CandidateStore") as mock_store_cls,
            patch("auto_reddit.main.settings") as mock_settings,
            patch("auto_reddit.main.deliver_daily"),
        ):
            # Force weekday (Wednesday) to bypass weekend guard
            mock_dt.date.today.return_value = _datetime.date(2026, 3, 25)
            mock_settings.db_path = ":memory:"
            mock_settings.daily_review_limit = 8
            mock_settings.deepseek_model = "deepseek-chat"
            mock_store_cls.return_value = mock_store
            mock_collect.return_value = []
            mock_fetch.return_value = []
            mock_eval.return_value = [accepted, rejected]

            from auto_reddit.main import run

            run()

        mock_store.save_pending_delivery.assert_called_once_with(
            "post_a", accepted.model_dump_json()
        )
        mock_store.save_rejected.assert_called_once_with("post_b")


# ---------------------------------------------------------------------------
# Additional: verify system prompt and user message builders
# ---------------------------------------------------------------------------


class TestPromptBuilders:
    def test_system_prompt_contains_key_rules(self):
        prompt = _build_system_prompt()
        assert (
            "abstención" in prompt.lower()
            or "abstenci" in prompt.lower()
            or "NO intervenir" in prompt
            or "no intervenir" in prompt.lower()
        )
        assert "funcionalidad" in prompt
        assert "desarrollo" in prompt
        assert "dudas_si_merece_la_pena" in prompt
        assert "comparativas" in prompt
        assert "resolved_or_closed" in prompt
        assert "no_useful_contribution" in prompt
        assert "excluded_topic" in prompt
        assert "insufficient_evidence" in prompt
        assert "json" in prompt.lower()

    def test_system_prompt_contains_two_phase_instruction(self):
        prompt = _build_system_prompt()
        # Two-phase: decide first, generate second
        assert "FASE 1" in prompt or "fase 1" in prompt.lower()
        assert "FASE 2" in prompt or "fase 2" in prompt.lower()

    def test_system_prompt_contains_opportunity_reason_field(self):
        prompt = _build_system_prompt()
        assert "opportunity_reason" in prompt

    def test_system_prompt_contains_anti_reverse_justification_rule(self):
        prompt = _build_system_prompt()
        # Rule: do not accept only because a plausible answer could be written
        assert (
            "plausible" in prompt.lower()
            or "racionalizar" in prompt.lower()
            or "plausib" in prompt.lower()
        )

    def test_system_prompt_contains_response_length_guidance(self):
        prompt = _build_system_prompt()
        # 2-6 sentences guidance
        assert "2" in prompt and "6" in prompt and "frase" in prompt.lower()

    def test_system_prompt_contains_halltic_guardrail(self):
        prompt = _build_system_prompt()
        # Halltic: never as pitch, never unprompted
        assert "halltic" in prompt.lower() or "Halltic" in prompt
        assert "NUNCA" in prompt or "nunca" in prompt.lower()

    def test_system_prompt_contains_null_comment_summary_instruction(self):
        prompt = _build_system_prompt()
        assert "null" in prompt.lower() or "none" in prompt.lower()
        assert "comment_summary_es" in prompt

    def test_system_prompt_uses_single_json_root(self):
        prompt = _build_system_prompt()
        # No separate floating JSON block for degraded context — inline in root
        assert (
            "único objeto" in prompt.lower()
            or "un único objeto" in prompt.lower()
            or "único objeto raíz" in prompt.lower()
        )

    def test_user_message_contains_candidate_fields(self):
        ctx = _make_thread_context()
        msg = _build_user_message(ctx)
        assert "How do I configure Odoo Sales module?" in msg
        assert "https://www.reddit.com/r/Odoo/comments/post_001/" in msg
        assert "Odoo" in msg
        assert "full" in msg  # quality

    def test_user_message_contains_comment_body(self):
        ctx = _make_thread_context()
        msg = _build_user_message(ctx)
        assert "Have you tried going to Settings?" in msg

    def test_user_message_no_comments_shows_placeholder(self):
        ctx = _make_thread_context(comments=[])
        ctx = ThreadContext(
            candidate=_make_candidate(),
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit3",
        )
        msg = _build_user_message(ctx)
        assert (
            "ninguno" in msg.lower()
            or "no comments" in msg.lower()
            or "ninguno disponible" in msg
        )

    def test_user_message_degraded_context_includes_aviso(self):
        ctx = _make_thread_context(quality=ContextQuality.degraded)
        msg = _build_user_message(ctx)
        assert "degraded" in msg.lower() or "degradado" in msg.lower()
