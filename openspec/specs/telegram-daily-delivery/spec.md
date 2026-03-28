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

The system MUST apply a daily delivery cap of 8 opportunity messages. Retryable valid `pending_delivery` records MUST be prioritized before newly accepted unsent records, and the selected set SHALL be deterministic from persisted state alone.

#### Scenario: Retry backlog consumes the daily cap first

- GIVEN more than 8 valid retryable `pending_delivery` records exist
- WHEN the daily delivery step selects today’s opportunities
- THEN only 8 retry records are selected
- AND no new accepted record is delivered that day

#### Scenario: Remaining capacity is filled with new opportunities

- GIVEN 3 valid retryable `pending_delivery` records and 6 new accepted unsent records exist
- WHEN the daily delivery step selects today’s opportunities
- THEN the 3 retries are selected first
- AND only 5 new records are added to reach the cap of 8

### Requirement: Send Telegram messages with HTML formatting and non-blocking summary

The system MUST render Telegram opportunity messages deterministically from persisted `opportunity_data` and MUST send them using Telegram HTML parse mode. The system SHOULD send one summary message before individual opportunity messages, but summary failure MUST NOT block the opportunity deliveries.

#### Scenario: Summary succeeds before opportunity delivery

- GIVEN the daily run has selected opportunity messages to send
- WHEN the summary message is accepted by Telegram
- THEN the summary is sent first
- AND the individual opportunity messages are still sent afterward in the selected order

#### Scenario: Summary failure does not stop opportunity delivery

- GIVEN the daily run has selected opportunity messages to send
- WHEN the summary message fails to send
- THEN the failure is recorded as non-blocking
- AND the individual opportunity messages are still attempted

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
