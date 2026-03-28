# operational-integration-tests Specification

## Purpose

Define operational integration coverage for the existing `main.run()` pipeline so runtime orchestration can be verified without adding product behavior or refactoring production boundaries.

## Requirements

### Requirement: Prove retry reuse from persisted accepted records

The test suite MUST prove that a `pending_delivery` record with valid persisted `opportunity_data` is retried through the real orchestration path, MUST reuse that persisted data as delivery input, and MUST NOT trigger AI re-evaluation during that retry.

#### Scenario: Retry delivery without AI re-evaluation

- GIVEN a real SQLite store contains a valid `pending_delivery` record
- WHEN `main.run()` executes with AI evaluation patched as a failing sentinel
- THEN delivery succeeds from persisted `opportunity_data`
- AND the AI evaluation boundary is not invoked

### Requirement: Prove delivery stays inside the delivery boundary

Operational integration tests MUST prove that the delivery phase consumes only eligible persisted delivery records and MUST NOT produce upstream side effects (Reddit collection, thread-context extraction, AI evaluation, or autonomous publishing). Because `main.run()` unconditionally traverses the full orchestration pipeline on every invocation, the accepted proof strategy is to patch upstream boundaries to return empty/controlled input — so those phases execute with zero effect — and assert that delivery output comes exclusively from the pre-inserted persisted delivery set. Refactoring `main.run()` to make those phases skippable is explicitly out of scope.

#### Scenario: Delivery processes retries without upstream re-entry

- GIVEN `main.run()` reaches delivery with upstream boundaries patched to return empty/controlled input
- AND a `pending_delivery` record exists in real SQLite before the run
- WHEN `main.run()` executes
- THEN delivery reads only the persisted delivery set
- AND upstream phases produce no collection, extraction, evaluation, or publishing side effect (empty-input traversal is expected and acceptable)

### Requirement: Prove evaluation stays isolated from Reddit and delivery side effects

Operational integration tests MUST prove that AI opportunity evaluation consumes only normalized upstream thread context, MUST NOT trigger Reddit collection or delivery side effects, and SHALL fail if those external boundaries are touched while evaluation behavior is being exercised.

#### Scenario: Evaluation executes without delivery or Reddit side effects

- GIVEN evaluation receives controlled normalized thread-context input
- WHEN Reddit and delivery boundaries are patched as sentinels
- THEN evaluation returns its bounded outcome from that input only
- AND no Reddit or delivery side effect occurs

### Requirement: Prove multi-run operational memory boundaries

Operational integration tests MUST use real SQLite state across multiple runs to prove that `sent` and `rejected` records are excluded from later daily review, while valid `pending_delivery` records remain retryable and are not treated as final exclusions.

#### Scenario: Final decisions exclude later review while retry records remain eligible

- GIVEN one run persists `sent`, `rejected`, and `pending_delivery` outcomes in real SQLite
- WHEN a later run executes against the same store
- THEN `sent` and `rejected` posts are excluded from daily review
- AND valid `pending_delivery` records remain available for delivery retry without AI re-evaluation

### Requirement: Keep operational, unit, and smoke-test boundaries explicit

This change MUST add only operationally scoped verification around existing external integrations, MUST NOT redefine unit-test responsibilities, and MUST NOT change delivery feature behavior. Optional smoke tests MAY cover Reddit and Telegram only when they are env-gated by dedicated smoke-only variables, skipped by default, and non-blocking for normal `uv run pytest tests/ -x --tb=short` runs. Telegram smoke coverage MUST stay limited to manual verification of the existing `send_message()` integration against a controlled non-production bot/chat.

#### Scenario: Telegram smoke tests stay skipped in standard runs

- GIVEN `TELEGRAM_SMOKE_BOT_TOKEN` or `TELEGRAM_SMOKE_CHAT_ID` is absent
- WHEN the integration test suite runs normally
- THEN Telegram smoke coverage is skipped by default
- AND standard verification remains successful without manual credentials

#### Scenario: Manual Telegram smoke verifies the existing delivery boundary only

- GIVEN dedicated `TELEGRAM_SMOKE_*` credentials target a controlled non-production Telegram chat
- WHEN a developer runs the integration suite manually with those variables set
- THEN the smoke test verifies real `send_message()` delivery for the existing Telegram integration
- AND no new unit-test scope, pipeline-wide smoke scope, or production behavior change is introduced

#### Scenario: Production delivery credentials are not the smoke-test contract

- GIVEN normal `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` exist without `TELEGRAM_SMOKE_*`
- WHEN the smoke-capable integration suite runs
- THEN Telegram smoke coverage does not treat production delivery credentials as its activation contract
- AND the smoke verification remains opt-in and isolated from live delivery configuration
