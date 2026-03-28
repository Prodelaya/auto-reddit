# Archive Report

**Change**: telegram-smoke-tests  
**Mode**: hybrid  
**Archived on**: 2026-03-28

## Archive Decision

Archive approved. The final verify outcome is **PASS** with **no critical issues, warnings, or suggestions**. The successful live Telegram smoke execution is preserved as the acceptance proof for the real `send_message()` boundary: plain-text delivery passed, invalid-token handling returned `False` as designed, and HTML delivery passed against the controlled non-production Telegram channel.

## Final Verify Outcome Preserved

- **Verdict**: PASS
- **Full suite**: `uv run pytest tests/ -x --tb=short` → 273 passed in 30.25s
- **Live Telegram smoke run**: `uv run pytest tests/test_integration/test_operational.py -k "TestTelegramSmokeOptional" -v --tb=long` → 3 passed, 11 deselected in 4.53s
- **Live proof preserved**:
  - `test_send_message_delivers_plain_text` → ✅ PASS
  - `test_send_message_returns_false_for_invalid_token` → ✅ PASS
  - `test_send_message_delivers_html_formatting` → ✅ PASS
- **Operational boundary note preserved**: Telegram smoke coverage remains opt-in, env-gated by `TELEGRAM_SMOKE_BOT_TOKEN` and `TELEGRAM_SMOKE_CHAT_ID`, skipped by default in standard runs, and isolated from production `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

## Spec Sync

| Domain | Action | Details |
|--------|--------|---------|
| `operational-integration-tests` | Updated | Replaced the smoke-boundary requirement in `openspec/specs/operational-integration-tests/spec.md` to include Telegram smoke gating, live-boundary verification, and the rule that production delivery credentials are not the smoke activation contract. |

## Artifact Lineage

- Project context (Engram): `#735` → `sdd-init/auto-reddit`
- Proposal (Engram): `#1387` → `sdd/telegram-smoke-tests/proposal`
- Spec (Engram): `#1389` → `sdd/telegram-smoke-tests/spec`
- Design (Engram): `#1392` → `sdd/telegram-smoke-tests/design`
- Tasks (Engram): `#1394` → `sdd/telegram-smoke-tests/tasks`
- Apply progress (Engram): `#1396` → `sdd/telegram-smoke-tests/apply-progress`
- Verify report (Engram): `#1399` → `sdd/telegram-smoke-tests/verify-report`

## Hybrid Traceability Note

The archive preserves both the consolidated main spec and the final filesystem artifacts for proposal, specs, design, tasks, verify, and archive reporting. The audit trail explicitly records that the change reached **PASS** only after the live Telegram smoke run succeeded with controlled non-production credentials.
