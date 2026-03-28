# Proposal: AI Opportunity Evaluation

## Intent

Add the evaluation step that takes already-selected `ThreadContext` inputs, decides whether each post is a valid Odoo opportunity, and persists structured AI output for human review and later deterministic delivery.

## Scope

### In Scope
- Evaluate only upstream-provided normalized `ThreadContext` items.
- Return structured accepted/rejected results, including distinct rejection types.
- Persist accepted evaluations as structured `opportunity_data` for retry-safe downstream delivery without re-evaluating AI.
- Preserve context-quality rules: `partial` allows normal evaluation; `degraded` allows evaluation with warning plus human-review bullets.

### Out of Scope
- Reddit collection, daily slicing, or thread-context extraction.
- Telegram message formatting, Telegram retry rendering, or autonomous publishing.
- New business states such as `approved`, backlog queues, or `insufficient_evidence` outputs.

## Approach

Invoke DeepSeek after thread-context extraction, apply existing product/style rules, and emit a bounded structured contract for either acceptance or rejection. Keep prudence inside the evaluation itself rather than adding a third outcome type.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auto_reddit/evaluation/` | New/Modified | AI opportunity evaluation flow and structured result generation |
| `src/auto_reddit/persistence/` | Modified | Persistence of accepted structured output and rejected outcomes |
| `src/auto_reddit/delivery/` | Modified | Consume persisted structured output later without re-evaluating AI |
| `openspec/changes/ai-opportunity-evaluation/` | New/Modified | Proposal and follow-on SDD artifacts |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| AI overstates certainty on weak context | Medium | Encode prudence rules and explicit degraded warnings |
| Scope drifts into Telegram formatting | Medium | Keep delivery rendering out of this change |
| Output contract is too presentation-specific | Medium | Persist structured fields, not final Telegram strings |

## Rollback Plan

Disable the new evaluation step and fall back to the current pre-evaluation pipeline boundary, removing any new persistence usage while preserving upstream collection/context changes.

## Dependencies

- Upstream specs: `reddit-candidate-collection`, `candidate-memory`, `thread-context-extraction`
- Product rules in `docs/product/product.md` and `docs/product/ai-style.md`

## Success Criteria

- [ ] Only normalized upstream `ThreadContext` items are evaluated.
- [ ] Accepted results include structured delivery-ready data; rejected results include rejection type.
- [ ] `partial` and `degraded` quality follow the confirmed review semantics.
- [ ] Telegram retries reuse persisted structured output without a new AI evaluation.
