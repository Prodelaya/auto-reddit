# Tasks: AI Opportunity Evaluation

## Phase 1: Foundation — Contracts & Config

- [x] 1.1 Add `OpportunityType` enum to `src/auto_reddit/shared/contracts.py` with values: `funcionalidad`, `desarrollo`, `dudas_si_merece_la_pena`, `comparativas`
- [x] 1.2 Add `RejectionType` enum to `src/auto_reddit/shared/contracts.py` with values: `resolved_or_closed`, `no_useful_contribution`, `excluded_topic`, `insufficient_evidence`
- [x] 1.3 Add `AIRawResponse` Pydantic model to `contracts.py` — what DeepSeek returns: `accept: bool`, conditional fields for accepted (`opportunity_type`, `opportunity_reason`, `post_summary_es`, `comment_summary_es`, `suggested_response_es`, `suggested_response_en`, `post_language`), conditional fields for rejected (`rejection_type`), optional `warning`, optional `human_review_bullets: list[str]`
- [x] 1.4 Add `AcceptedOpportunity` model to `contracts.py` — merges pipeline deterministic fields (`post_id`, `title`, `link`, `post_language`) + AI fields. `opportunity_reason: str` required. `comment_summary_es: str | None`. Validate: `model_dump_json()` produces valid `opportunity_data` for persistence
- [x] 1.5 Add `RejectedPost` model to `contracts.py` with `post_id` + `rejection_type: RejectionType`
- [x] 1.6 Define `EvaluationResult = AcceptedOpportunity | RejectedPost` union in `contracts.py`
- [x] 1.7 Add `deepseek_model: str = "deepseek-chat"` field to `Settings` in `src/auto_reddit/config/settings.py`
- [x] 1.8 Add `tenacity` dependency: `uv add tenacity`

## Phase 2: Core Implementation — Evaluator

- [x] 2.1 Implement `_build_system_prompt() -> str` in `src/auto_reddit/evaluation/evaluator.py` — static prompt encoding: prudent evaluator role, two-phase process (decide then generate), abstention-first, anti-reverse-justification rule, Reddit-native helper tone, Halltic guardrail (never as pitch/unprompted), response length 2-6 sentences, nullable comment_summary_es instruction, closed enums, inline JSON examples (accept/reject × normal/degraded). Reference `docs/product/ai-style.md` for tone rules
- [x] 2.2 Implement `_build_user_message(ctx: ThreadContext) -> str` in `evaluator.py` — deterministic serialization of `ThreadContext` fields (candidate title, selftext, url, subreddit, comments, quality). Do NOT ask model for deterministic fields
- [x] 2.3 Implement `_evaluate_single(ctx: ThreadContext, client: OpenAI, model: str) -> EvaluationResult` in `evaluator.py` — call DeepSeek with `response_format={"type": "json_object"}`, parse JSON, validate with `AIRawResponse`, merge deterministic fields, return `AcceptedOpportunity` or `RejectedPost`. Add degraded-context warning + `human_review_bullets` when `ctx.quality == degraded`
- [x] 2.4 Wrap `_evaluate_single` with tenacity retry (3 attempts, exponential backoff). On permanent failure / parse error / validation error: log warning, return `None` (skip post — NOT rejected)
- [x] 2.5 Implement `evaluate_batch(contexts: list[ThreadContext], settings: Settings) -> list[EvaluationResult]` — init OpenAI client once, iterate contexts calling `_evaluate_single`, collect non-None results. Log skipped count. Empty input → empty output with warning

## Phase 3: Integration — Wire in main.py

- [x] 3.1 Update `src/auto_reddit/evaluation/__init__.py` to export `evaluate_batch`
- [x] 3.2 Replace Change 4 placeholder in `src/auto_reddit/main.py`: call `evaluate_batch(thread_contexts, settings)`, loop results — `AcceptedOpportunity` → `store.save_pending_delivery(r.post_id, r.model_dump_json())`, `RejectedPost` → `store.save_rejected(r.post_id)`. Log accepted/rejected/skipped counts

## Phase 4: Testing

- [x] 4.1 Create `tests/test_evaluation/test_contracts.py` — validate `AIRawResponse` accepts valid accepted/rejected JSON, rejects missing fields, rejects invalid enum values. Verify `AcceptedOpportunity.model_dump_json()` round-trips cleanly
- [x] 4.2 Create `tests/test_evaluation/test_evaluator.py` — mock `OpenAI.chat.completions.create`. Test: valid accepted response → `AcceptedOpportunity`, valid rejected response → `RejectedPost`, degraded context → warning + human_review_bullets present, invalid JSON → skip (None), API error after retries → skip (None)
- [x] 4.3 Add `test_evaluate_batch_empty_input` — empty list → empty list, no API calls
- [x] 4.4 Add `test_evaluate_batch_mixed_results` — batch with 1 accept, 1 reject, 1 failure → returns 2 results, skipped=1
- [x] 4.5 Add `test_main_integration` in `tests/test_evaluation/test_evaluator.py` — mock `evaluate_batch` return, verify `save_pending_delivery` called for accepted with JSON payload, `save_rejected` called for rejected

## Corrective Pass: Design-Implementation Alignment (post-apply)

- [x] C.1 Add `opportunity_reason: str | None` to `AIRawResponse` in `contracts.py`
- [x] C.2 Add `opportunity_reason: str` to `AcceptedOpportunity` in `contracts.py`
- [x] C.3 Change `comment_summary_es` from `str` to `str | None` in `AcceptedOpportunity`
- [x] C.4 Pass `opportunity_reason` and nullable `comment_summary_es` in `_evaluate_single_raw` constructors
- [x] C.5 Update system prompt: two-phase instruction (FASE 1 / FASE 2)
- [x] C.6 Update system prompt: include `opportunity_reason` in accept JSON example
- [x] C.7 Update system prompt: inline degraded-context fields in both accept and reject examples (no separate floating JSON block)
- [x] C.8 Update system prompt: anti-reverse-justification rule
- [x] C.9 Update system prompt: Halltic guardrail (NUNCA as pitch, NUNCA unprompted)
- [x] C.10 Update system prompt: response length guidance (2–6 frases) and null comment summary instruction
- [x] C.11 Update all tests to include `opportunity_reason` and nullable `comment_summary_es`
- [x] C.12 Add new tests: two-phase prompt, opportunity_reason, anti-reverse-justification, length guidance, Halltic guardrail, single JSON root, null comment_summary_es round-trip

## Post-Verify Corrective Pass: warning/bullets to accepted only

- [x] V.1 Fix system prompt: remove `warning`/`human_review_bullets` from the rejected-degraded JSON example; rejected example is now context-agnostic
- [x] V.2 Fix user message aviso: "si decides aceptar o rechazar" → "si decides aceptar" (degraded-context notice applies to accepted path only)
- [x] V.3 Clarify `AIRawResponse` docstring: warning/bullets only propagated to `AcceptedOpportunity`, not to `RejectedPost`
- [x] V.4 Clarify `AcceptedOpportunity` comment: degraded fields are accepted-only
- [x] V.5 Rename test `test_degraded_context_rejected_includes_warning_and_bullets` → `test_degraded_context_rejected_has_no_warning_or_bullets`; add explicit `hasattr` assertions proving no warning/bullets on `RejectedPost`
- [x] V.6 Add `TestEvaluateSinglePartialContext` with 3 tests: accepted has no warning/bullets, rejected is clean, user message has no aviso for partial
- [x] V.7 Update `design.md` to align Principle 9, interfaces comment, and ADOPTED #3 with the user's authoritative clarification
- [x] V.8 Update spec requirement text and scenarios for degraded context to reflect accepted-only rule; add new "Rejected degraded context carries no warning or bullets" scenario

**Status: 18 original + 12 corrective + 8 post-verify = 38/38 tasks complete. All verify issues resolved. 163/163 tests pass.**
