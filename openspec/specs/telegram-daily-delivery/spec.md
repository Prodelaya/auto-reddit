# telegram-daily-delivery Specification

## Purpose

Define the deterministic daily Telegram delivery of persisted accepted opportunities for human review, without re-running AI or introducing autonomous publishing behavior.

## Requirements

### Requirement: Deliver only persisted accepted opportunities within the review boundary

The system MUST select delivery candidates only from persisted accepted records that remain in `pending_delivery` and contain structured `opportunity_data`. The system MUST reuse that persisted data as the delivery source of truth, MUST NOT trigger AI evaluation or re-evaluation during delivery, and MUST NOT create editorial backlog or autonomous Reddit publishing behavior.

#### Scenario: Deliver from persisted accepted records only

- GIVEN accepted records exist in `pending_delivery` with structured `opportunity_data`
- WHEN the daily delivery step runs
- THEN only those persisted records are eligible for Telegram delivery
- AND no AI call or Reddit publishing action occurs

#### Scenario: Exclude records outside the delivery boundary

- GIVEN a record is not in `pending_delivery` or lacks valid structured `opportunity_data`
- WHEN the daily delivery step builds the candidate set
- THEN that record is not selected for Telegram delivery

### Requirement: Apply deterministic retry-first selection within the daily cap

The system MUST apply a daily delivery cap equal to the configured `max_daily_opportunities`. Retryable valid `pending_delivery` records MUST be prioritized before newly accepted unsent records, and runtime plus documentation MUST NOT define different effective caps.

#### Scenario: Runtime enforces the configured cap

- GIVEN `max_daily_opportunities` is 8 and 10 valid delivery candidates exist
- WHEN the daily delivery step selects today’s opportunities
- THEN exactly 8 opportunities are selected

#### Scenario: Lowering the cap reduces the same-day selection

- GIVEN `max_daily_opportunities` is 3 and 5 valid delivery candidates exist
- WHEN the daily delivery step selects today’s opportunities
- THEN exactly 3 opportunities are selected

### Requirement: Send Telegram messages with daily summary coverage

The system MUST render Telegram opportunity messages deterministically from persisted `opportunity_data` and MUST send them using Telegram HTML parse mode. The system MUST emit exactly one daily summary for every executed weekday run, including when 0 opportunities are selected. When summary delivery succeeds, it MUST precede any individual opportunity messages. Summary failure MUST NOT block opportunity deliveries.

#### Scenario: Zero-opportunity weekday run still emits a summary

- GIVEN an executed weekday daily run selects 0 opportunities
- WHEN the delivery phase finishes selection
- THEN one daily summary is emitted stating the 0-opportunity outcome
- AND no individual opportunity message is sent

#### Scenario: Summary failure does not stop selected deliveries

- GIVEN an executed weekday daily run selects one or more opportunities
- WHEN the summary message fails to send
- THEN the failure is treated as non-blocking
- AND the selected opportunity messages are still attempted

### Requirement: Close records only on Telegram success and retry until TTL expiry

The system MUST mark a record as `sent` only after successful Telegram delivery of that opportunity message. Failed deliveries MUST remain retryable indefinitely while the record stays valid. The system MUST expire `pending_delivery` validity using this TTL rule: records created on Monday, Tuesday, or Wednesday remain valid until Friday; records created on Thursday or Friday remain valid until the next Monday.

#### Scenario: Successful opportunity delivery closes the record

- GIVEN a selected `pending_delivery` record is sent successfully to Telegram
- WHEN Telegram confirms the opportunity message delivery
- THEN the record is marked as `sent`

#### Scenario: Failed or expired records are not closed incorrectly

- GIVEN a selected `pending_delivery` record either fails delivery or has exceeded its weekly TTL window
- WHEN the delivery step completes
- THEN a failed but still valid record remains retryable in `pending_delivery`
- AND an expired record is excluded from further delivery attempts
