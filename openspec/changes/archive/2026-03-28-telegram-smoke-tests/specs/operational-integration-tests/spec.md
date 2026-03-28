# Delta for operational-integration-tests

## MODIFIED Requirements

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
