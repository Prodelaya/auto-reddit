# Proposal: Telegram Daily Delivery

## Intent

Deliver persisted accepted opportunities to Telegram in a deterministic daily step, closing the gap between accepted AI output and human review without re-running AI or introducing editorial backlog behavior.

## Scope

### In Scope
- Send up to 8 daily Telegram opportunity messages using persisted accepted records as the source of truth.
- Prioritize valid retryable `pending_delivery` records before new deliveries, with indefinite retries while the record remains valid.
- Mark records as `sent` only after successful Telegram delivery, using HTML parse mode and a non-blocking summary-first pattern.
- Expire stale `pending_delivery` records with the weekly TTL rule: Mon/Tue/Wed→Friday, Thu/Fri→next Monday.

### Out of Scope
- Any new AI evaluation, re-evaluation, or DeepSeek calls during delivery.
- Editorial backlog management, approval workflows, or autonomous Reddit publishing.
- Changes to upstream collection, context extraction, or evaluation semantics beyond consuming their persisted outputs.

## Approach

Add a delivery slice that reads persisted structured evaluation data, renders deterministic Telegram-ready content, and executes a daily send cycle with retry-first ordering inside the cap. Delivery remains operationally separate from evaluation so transport failures do not change business verdicts.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auto_reddit/delivery/` | Modified | Daily delivery selection, rendering, Telegram send flow |
| `src/auto_reddit/persistence/` | Modified | Retry eligibility, TTL handling, sent-after-success persistence |
| `src/auto_reddit/main.py` | Modified | Wire the deterministic delivery step into the daily run |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Retry ordering or cap mishandled | Medium | Define proposal/spec rules for retry-first and cap-of-8 behavior |
| Premature `sent` state | Medium | Keep success confirmation as the only close condition |
| HTML formatting failures | Low | Constrain delivery to deterministic persisted fields |

## Rollback Plan

Disable the delivery step and keep accepted records in pre-send persistence; upstream collection, extraction, and AI evaluation remain unchanged.

## Dependencies

- Persisted accepted opportunity data from `candidate-memory` and `ai-opportunity-evaluation`
- Telegram Bot API credentials and existing runtime configuration

## Success Criteria

- [ ] Daily delivery sends at most 8 opportunities with retries processed before new items.
- [ ] Delivery reuses persisted structured evaluation and never triggers AI evaluation.
- [ ] Records move to `sent` only after Telegram success; failed deliveries remain retryable until TTL expiry.
