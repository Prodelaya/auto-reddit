# Delta for telegram-daily-delivery

## MODIFIED Requirements

### Requirement: Apply deterministic retry-first selection within the daily cap

The system MUST apply a daily delivery cap equal to the configured `max_daily_opportunities`. Retryable valid `pending_delivery` records MUST be prioritized before newly accepted unsent records, and runtime plus documentation MUST NOT define different effective caps.

(Previously: The system MUST apply a daily delivery cap of 8 opportunity messages.)

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

(Previously: The system SHOULD send one summary message before individual opportunity messages, but summary failure MUST NOT block the opportunity deliveries.)

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
