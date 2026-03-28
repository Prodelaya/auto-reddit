# Design: AI Opportunity Evaluation (Refined)

## Technical Approach

Implement `evaluation/evaluator.py` as a pure evaluation function that takes `list[ThreadContext]`, calls DeepSeek once per item, validates the structured JSON response with Pydantic, and returns a list of typed results. `main.py` orchestrates persistence (accepted → `save_pending_delivery`, rejected → `save_rejected`). Prompt is a static system message encoding all product/style rules; the user message is built deterministically from `ThreadContext` fields.

This refinement addresses analyst feedback on prompt structure, contract naming alignment, degraded-context behavior, and the `opportunity_reason` field.

## Architecture Decisions

| Decision | Alternatives | Rationale |
|----------|-------------|-----------|
| **`deepseek-chat` (non-thinking)** | `deepseek-reasoner` (R1) | Task is classification + synthesis, not formal reasoning. Better tone control, lower latency, cheaper. `ai-style.md` §13 confirms. |
| **`json_object` mode + Pydantic validation** | `json_schema` strict mode, or free-text parsing | DeepSeek supports `response_format: {type: json_object}` on stable endpoint. `json_schema` only exists for tool calls on `/beta`. Pydantic validation post-parse catches schema violations and gives clear errors. |
| **One API call per ThreadContext** | Batch all in one call | Each post needs individual accept/reject; batching risks partial parse failures losing the entire batch. Individual calls allow per-post skip on failure. |
| **Static system prompt + deterministic user message** | Dynamic system prompt per post | System prompt is cacheable by DeepSeek (prefix cache). Deterministic fields (`post_id`, `title`, `link`) are NOT requested from the model — set by pipeline from `ThreadContext`. |
| **Per-post skip on DeepSeek failure** | Halt entire pipeline | Human decision: DeepSeek failure for one post skips that post without final business rejection. Transient errors retry (tenacity); persistent errors log and skip. Post remains undecided — eligible tomorrow. |
| **Evaluation returns results; `main.py` persists** | Evaluator calls store directly | `python-conventions` skill: evaluation module does NOT persist. `main.py` is the only orchestrator. |
| **`EvaluationResult` discriminated union** | Single flat model with optional fields | Clean separation: `AcceptedOpportunity` vs `RejectedPost` with `rejection_type` enum. `model_dump_json()` on accepted goes straight to `opportunity_data`. |
| **Single JSON root object always** | Separate accept/reject schemas | One schema with conditional fields. DeepSeek returns one JSON object; Pydantic validates the shape post-parse. No floating fragments. |
| **Add `opportunity_reason` to accepted output** | Rely on post_summary_es alone | Summaries describe the post; `opportunity_reason` explains WHY intervention is warranted. Different purpose — human reviewer needs both to decide. |
| **Explicit two-phase prompt: decide then generate** | Let model interleave decision and content | Forces the model to resolve accept/reject BEFORE composing content fields. Reduces hallucinated acceptances where the model generates a plausible response and then rationalizes acceptance around it. |

## Data Flow

```
main.py
  │
  │  list[ThreadContext]
  ▼
evaluate_batch(contexts, settings)        ← evaluation/evaluator.py
  │
  │  for each ThreadContext:
  │    ├─ build_user_message(ctx)         ← deterministic fields + comments
  │    ├─ client.chat.completions.create  ← DeepSeek API
  │    ├─ json.loads + Pydantic validate  ← AIRawResponse model
  │    ├─ merge deterministic fields      ← AcceptedOpportunity | RejectedPost
  │    └─ on API failure: retry → skip (log warning, continue)
  │
  │  list[EvaluationResult]
  ▼
main.py
  ├─ accepted → store.save_pending_delivery(post_id, result.model_dump_json())
  └─ rejected → store.save_rejected(post_id)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/shared/contracts.py` | Modify | Fix `OpportunityType` enum values to match `product.md` taxonomy, add `opportunity_reason` to `AIRawResponse` + `AcceptedOpportunity`, unify `warning` field name, allow `comment_summary_es` to be `None` |
| `src/auto_reddit/evaluation/evaluator.py` | Modify | Update system prompt with two-phase instruction, degraded-context behavioral rules, `opportunity_reason`, Halltic guardrail, response length guidance, comment-summary null allowance |
| `src/auto_reddit/evaluation/__init__.py` | No change | Already exports `evaluate_batch` |
| `src/auto_reddit/config/settings.py` | No change | `deepseek_model` already present |
| `src/auto_reddit/main.py` | No change | Wiring already in place from initial apply |

## Interfaces / Contracts (Refined)

```python
# --- Enums (shared/contracts.py) ---

class OpportunityType(str, Enum):
    """Taxonomía cerrada — values match product.md §10 exactly."""
    funcionalidad = "funcionalidad"
    desarrollo = "desarrollo"
    dudas_si_merece_la_pena = "dudas_si_merece_la_pena"
    comparativas = "comparativas"

class RejectionType(str, Enum):
    """Tipos de rechazo — closed enum."""
    resolved_or_closed = "resolved_or_closed"
    no_useful_contribution = "no_useful_contribution"
    excluded_topic = "excluded_topic"
    insufficient_evidence = "insufficient_evidence"

# --- AI raw response (what DeepSeek returns) ---

class AIRawResponse(BaseModel):
    accept: bool

    # Acceptance fields (required when accept=True)
    opportunity_type: OpportunityType | None = None
    opportunity_reason: str | None = None        # NEW: why intervention is warranted
    post_language: str | None = None
    post_summary_es: str | None = None
    comment_summary_es: str | None = None        # None allowed when no useful comments
    suggested_response_es: str | None = None
    suggested_response_en: str | None = None

    # Rejection fields (required when accept=False)
    rejection_type: RejectionType | None = None

    # Degraded context — present in raw response; propagated to AcceptedOpportunity only.
    # RejectedPost never carries these fields.
    warning: str | None = None                   # RENAMED: was degraded_context_warning in design v1
    human_review_bullets: list[str] | None = None

# --- Pipeline output contracts ---

class AcceptedOpportunity(BaseModel):
    # Pipeline-deterministic fields
    post_id: str
    title: str
    link: str

    # AI-generated fields
    post_language: str
    opportunity_type: OpportunityType
    opportunity_reason: str                      # NEW
    post_summary_es: str
    comment_summary_es: str | None               # CHANGED: None when no useful comments
    suggested_response_es: str
    suggested_response_en: str

    # Degraded context — ONLY on accepted opportunities (quality=degraded).
    # Rejected posts never carry warning or bullets.
    warning: str | None = None
    human_review_bullets: list[str] | None = None

class RejectedPost(BaseModel):
    post_id: str
    rejection_type: RejectionType

EvaluationResult = AcceptedOpportunity | RejectedPost
```

### Key contract changes from v1

1. **`opportunity_reason: str`** — new required field on accepted results. Explains WHY the model considers this an intervention opportunity, distinct from the post summary.
2. **`comment_summary_es: str | None`** — changed from required `str` to optional. When a post has zero comments or comments add no useful context, the model returns `null` instead of fabricating a summary.
3. **`warning`** — field name unified. The design v1 used `degraded_context_warning` in the Interfaces section but `warning` in the prompt JSON examples and the actual implementation. The canonical name is `warning`.
4. **`OpportunityType` enum values** — the design v1 Interfaces section showed long human-readable values (`"funcionalidad y configuración de Odoo"`) but the implementation correctly uses short machine-friendly values (`"funcionalidad"`). This refinement aligns the design document to match the implementation and the prompt, which already uses the short form.

## Prompt Design Principles (Refined)

The system prompt encodes rules from `ai-style.md` and `product.md`. Refined principles:

1. **Role**: "Eres un evaluador prudente de oportunidades en r/Odoo y copiloto de respuesta para revisión humana. Tu sesgo por defecto es NO intervenir."
2. **Two-phase mental model (NEW)**: The prompt explicitly instructs: "PRIMERO decide si aceptas o rechazas. SOLO DESPUÉS, si aceptaste, genera los campos de contenido." This prevents the model from generating a plausible response and then reverse-justifying acceptance.
3. **Abstention-first**: "Acepta SOLO con evidencia clara y suficiente. Ante la duda, rechaza."
4. **Acceptance must explain WHY (NEW)**: When accepting, `opportunity_reason` must state what specific value the intervention would add to the conversation — not just that a response is possible, but that it would honestly improve the thread.
5. **Tone for suggested_response**: "Suena como un forero habitual de Reddit, predispuesto por ayudar a la comunidad."
6. **Negative rules (explicit)**: No marketing. No reflexive Odoo defense. No overconfidence. No full implementations unless justified. No invented facts.
7. **Closure/redundancy check**: Evaluate whether thread is resolved/closed BEFORE considering acceptance. Use `product.md` §8 definition.
8. **Context sufficiency**: Evaluate whether available evidence is sufficient. Reject with `insufficient_evidence` if not.
9. **Degraded context — behavioral rule (CLARIFIED)**: When user message says `CALIDAD DEL CONTEXTO: degraded`, the model MUST apply reinforced prudence — raise the bar for acceptance. When the post is **accepted**, the model MUST include `warning` and `human_review_bullets` in the JSON. When the post is **rejected**, no warning or bullets are expected or surfaced — `RejectedPost` intentionally carries only `post_id` and `rejection_type`. The model does NOT receive a different system prompt; it receives the quality indicator in the user message and follows this behavioral rule for the accepted path only.
10. **Comment summary nullability (NEW)**: When no comments exist or comments add no useful context, `comment_summary_es` MUST be `null`, not a fabricated summary.
11. **Halltic guardrail (CLARIFIED)**: Halltic may appear ONLY when the thread seeks a partner, professional, or specialized help AND the mention adds contextual value. Never as a pitch. Never unprompted.
12. **Response length guidance (NEW)**: Suggested responses should be 2–6 sentences. Enough to add value, short enough to sound like a real Reddit comment. Avoid wall-of-text answers.
13. **Closed taxonomy**: `opportunity_type` and `rejection_type` are closed enums — no free text.
14. **JSON schema example in prompt**: Single root JSON object with all fields. No floating fragments. Examples for both accept and reject paths.
15. **Do NOT ask the model for**: `post_id`, `title`, `link`, `comment_count` — pipeline-known.
16. **Do NOT accept only because a plausible answer could be written (NEW)**: Accept only if the response would honestly improve the conversation — not just because the model can construct one.

## Failure Handling

| Failure | Behavior |
|---------|----------|
| DeepSeek transient (rate limit, timeout, 5xx) | Retry with tenacity (3 attempts, exponential backoff). |
| DeepSeek permanent (401 auth, 400 bad request) | Log error, skip post. Post stays undecided — eligible tomorrow. |
| JSON parse failure | Log, skip post. Same as permanent API failure. |
| Pydantic validation failure | Log, skip post. Model returned invalid schema. |
| All posts in batch fail | Pipeline continues with empty accepted list. Logs warning. |

**Critical**: A skipped post is NOT persisted as `rejected`. It remains in no state — eligible for re-evaluation next run.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `AIRawResponse` validation including `opportunity_reason` and nullable `comment_summary_es` | Pydantic model tests with valid/invalid fixtures |
| Unit | `build_user_message()` output for all quality levels | Snapshot test on message structure |
| Unit | `evaluate_batch()` with mocked DeepSeek client | Mock `client.chat.completions.create`, test accept/reject routing, degraded warnings, skip-on-failure |
| Integration | Full `evaluate_batch()` → persistence in `main.py` | Mock DeepSeek, real SQLite store, verify `pending_delivery` and `rejected` records |

## Migration / Rollout

No migration required. Changes are contract refinements to existing code. `tenacity` already added.

## Analyst Feedback Disposition

### ADOPTED

| # | Suggestion | Rationale |
|---|-----------|-----------|
| 1 | Add `opportunity_reason` field | Distinct from summary — explains WHY intervention is warranted. Critical for human reviewer. |
| 2 | Two-phase prompt: decide first, generate second | Prevents reverse-justified acceptances. Cheap structural change with high impact. |
| 3 | Clarify degraded context behavioral rules | Was under-specified. Now explicit: reinforced prudence + mandatory warning/bullets on **accepted** outcomes only. Rejected outputs carry only post_id + rejection_type regardless of context quality (user clarification post-verify). |
| 4 | Allow `comment_summary_es` to be null | Honest handling when no comments or no useful comments exist. Prevents fabricated summaries. |
| 5 | Single JSON root object, no floating fragments | Already the intent, but the prompt showed degraded fields as a separate JSON block. Refined to show them inline in both accept and reject examples. |
| 6 | Halltic guardrail: only if contextually useful, never as pitch | Was in ai-style.md but under-emphasized in prompt. Now explicit prompt instruction. |
| 7 | Response length guidance (2–6 sentences) | Prevents wall-of-text answers that sound unnatural in Reddit. Light guardrail. |
| 8 | Align taxonomy naming: design doc ↔ code ↔ prompt | Design v1 Interfaces section had long human-readable values; implementation + prompt already use short machine values. Design doc now matches. |
| 9 | "Do not accept only because a plausible answer could be written" | Direct reinforcement of abstention-first. Already implied but now explicit in prompt. |

### REJECTED

| # | Suggestion | Rationale |
|---|-----------|-----------|
| 1 | Add `non_odoo_or_irrelevant` rejection type | Scope is r/Odoo only — non-Odoo posts are extremely unlikely. If encountered, `excluded_topic` already covers it. Adding this value adds a near-unused branch and complicates the enum without product value. |
| 2 | Add `prudence_level` field | Prudence is a behavioral instruction, not a model output. The model either accepts (with evidence) or rejects. Adding a prudence score creates a meta-judgment that invites gaming and doesn't help the human reviewer decide. The warning/bullets mechanism for degraded context is sufficient. |
| 3 | Add `confidence_note` field | Same reasoning as prudence_level. A confidence self-assessment from the model is unreliable and creates false signal. The human reviewer has the post summary, opportunity reason, and suggested response — that's the evidence. |
| 4 | Rename `insufficient_evidence` → `insufficient_context` | `insufficient_evidence` is more accurate. The model rejects because it lacks evidence to evaluate, not because the pipeline gave degraded context (which is a quality indicator, not a rejection). The names serve different purposes and shouldn't be conflated. |

### DEFERRED

| # | Suggestion | Rationale |
|---|-----------|-----------|
| 1 | Clarify boundary between `resolved_or_closed` and `no_useful_contribution` | These are conceptually distinct (thread is done vs. thread is open but we can't add value). In practice the model may struggle at the boundary. Deferring to verify phase — if real-world evaluation shows confusion, we can add prompt examples to clarify. Not a contract change. |

## Implementation Misalignment Report

The current implementation (already applied) has these misalignments with the refined design:

1. **`opportunity_reason` field missing** — `AIRawResponse` and `AcceptedOpportunity` in `contracts.py` lack this field. `evaluator.py` doesn't pass it. **Corrective apply required.**
2. **`comment_summary_es` is required `str` in `AcceptedOpportunity`** — should be `str | None`. **Corrective apply required.**
3. **System prompt lacks two-phase instruction** — "decide first, generate second" is not in `_SYSTEM_PROMPT_TEMPLATE`. **Corrective apply required.**
4. **System prompt shows degraded fields as separate JSON block** — lines 113–117 show `warning` and `human_review_bullets` as a separate `{{ }}` block after the accept/reject examples, which could confuse the model into returning two JSON objects. Must be inline in both accept and reject JSON examples. **Corrective apply required.**
5. **System prompt lacks "do not accept only because a plausible answer could be written" rule** — **Corrective apply required.**
6. **System prompt lacks Halltic explicit guardrail** — line 83 mentions it briefly but without the "never as a pitch, never unprompted" emphasis. **Corrective apply in prompt.**
7. **System prompt lacks response length guidance** — **Corrective apply in prompt.**
8. **System prompt lacks null comment_summary_es instruction** — **Corrective apply in prompt.**

**Verdict**: A corrective apply pass is required before verify. All misalignments are in `contracts.py` (2 fields) and `evaluator.py` (prompt text). No structural/architectural changes needed.

### Post-verify corrective pass (2026-03-28)

User clarification: `warning` and `human_review_bullets` apply ONLY to accepted opportunities. Rejected outputs (any context quality) never carry these fields. Changes applied:

- System prompt: removed rejected-degraded JSON template that showed `warning`/`bullets` on reject; rejected example is now context-agnostic (`{"accept": false, "rejection_type": "..."}`).
- User message aviso: changed "si decides aceptar o rechazar" → "si decides aceptar" for the degraded-context notice.
- `AIRawResponse` docstring: clarified that warning/bullets are only propagated to `AcceptedOpportunity`.
- `AcceptedOpportunity` comment: clarified scope as degraded accepted only.
- Tests: renamed `test_degraded_context_rejected_includes_warning_and_bullets` → `test_degraded_context_rejected_has_no_warning_or_bullets`, added explicit `hasattr` assertions. Added `TestEvaluateSinglePartialContext` class with 3 tests to close the untested spec scenario.
- This pass resolved all verify-reported issues (CRITICAL #1 and CRITICAL #2).

## Open Questions

None. All analyst feedback has been dispositioned.
