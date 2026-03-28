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

This change MUST add orchestration-focused operational integration tests only, MUST NOT redefine existing unit-test responsibilities, and MAY include Reddit smoke tests only when they are env-gated by `REDDIT_SMOKE_API_KEY`, skipped by default, and non-blocking for normal test runs.

#### Scenario: Optional smoke coverage does not block standard verification

- GIVEN `REDDIT_SMOKE_API_KEY` is absent in a normal test run
- WHEN the integration test suite is executed
- THEN optional smoke tests are skipped by default
- AND operational integration coverage remains the success criterion for the change
