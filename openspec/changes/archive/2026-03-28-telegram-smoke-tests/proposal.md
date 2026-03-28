# Proposal: Telegram Smoke Tests

## Intent

Add a small, manual smoke-test slice that proves the existing Telegram delivery integration still works with real Telegram credentials before deploys or after integration changes, without altering product behavior.

## Scope

### In Scope
- Add optional Telegram smoke coverage for `send_message()` using dedicated `TELEGRAM_SMOKE_BOT_TOKEN` and `TELEGRAM_SMOKE_CHAT_ID` credentials.
- Keep the tests env-gated, skipped by default, and non-blocking for normal `uv run pytest tests/ -x --tb=short` runs.
- Place the smoke coverage alongside existing operational smoke patterns in `tests/test_integration/test_operational.py`.

### Out of Scope
- Any production code or feature behavior changes.
- New unit-test coverage or broader end-to-end pipeline smoke coverage.
- Documenting smoke credentials in `.env.example`.

## Approach

Extend the established optional-smoke pattern already used for Reddit so developers can manually verify Telegram delivery against a controlled non-production bot/chat. The proposal keeps verification focused on the current integration boundary and avoids widening scope into delivery redesign or pipeline refactors.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/test_integration/test_operational.py` | Modified | Add optional Telegram smoke tests aligned with existing operational smoke conventions. |
| `openspec/changes/telegram-smoke-tests/proposal.md` | New | Capture intent, boundaries, and success criteria for this change. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Smoke credentials point to production chat | Low | Require dedicated `TELEGRAM_SMOKE_*` vars and identifiable smoke messages. |
| Real Telegram API flakiness causes noise | Medium | Keep tests manual, env-gated, and non-blocking. |

## Rollback Plan

Remove the optional Telegram smoke tests and restore `tests/test_integration/test_operational.py` to its prior Reddit-only smoke coverage.

## Dependencies

- Controlled Telegram bot token and test chat/channel where the bot is a member.
- Existing `send_message()` delivery integration and current operational smoke-test conventions.

## Success Criteria

- [ ] Manual Telegram smoke verification exists for real `send_message()` delivery using dedicated smoke credentials.
- [ ] Standard test runs still pass with Telegram smoke tests skipped by default.
- [ ] The change stays limited to test-only smoke verification with no production behavior changes.
