# Delta for candidate-memory

## MODIFIED Requirements

### Requirement: Preserve accepted opportunities for delivery retry

When AI accepts a post, the system MUST persist the structured evaluation output as the retry source of truth in `opportunity_data`, SHALL keep that pre-send record distinct from `sent`, and MUST reuse the persisted structured result for downstream deterministic rendering and Telegram retries without re-evaluating AI. (Previously: accepted opportunities only had to preserve a minimal retry-ready record distinct from `sent`.)

#### Scenario: Reuse persisted structured evaluation on retry

- GIVEN a post was accepted and its structured evaluation was persisted in `opportunity_data`
- WHEN a later delivery retry is attempted
- THEN downstream rendering uses that persisted structured evaluation
- AND no new AI evaluation is triggered
