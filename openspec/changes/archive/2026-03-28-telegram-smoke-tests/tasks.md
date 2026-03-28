# Tasks: Telegram Smoke Tests

## Phase 1: Foundation — Module-Level Variables

- [x] 1.1 Add `_SMOKE_TG_TOKEN = os.getenv("TELEGRAM_SMOKE_BOT_TOKEN")` and `_SMOKE_TG_CHAT_ID = os.getenv("TELEGRAM_SMOKE_CHAT_ID")` at module level in `tests/test_integration/test_operational.py`, after the existing `_SMOKE_API_KEY` line (line 805). Both use raw `os.getenv()` — no `Settings` model.

## Phase 2: Core Implementation — Test Class

- [x] 2.1 Add `TestTelegramSmokeOptional` class after `TestRedditSmokeOptional` (after line 839) in `test_operational.py`. Decorate with `@pytest.mark.skipif(not _SMOKE_TG_TOKEN or not _SMOKE_TG_CHAT_ID, reason="TELEGRAM_SMOKE_BOT_TOKEN / TELEGRAM_SMOKE_CHAT_ID not set — Telegram smoke skipped")`. Both vars required to activate.
- [x] 2.2 Implement `test_send_message_delivers_plain_text` (S1): import `send_message` from `auto_reddit.delivery.telegram`, call with `_SMOKE_TG_TOKEN`, `_SMOKE_TG_CHAT_ID`, plain text prefixed `"🧪 auto-reddit smoke test — plain"`, assert returns `True`.
- [x] 2.3 Implement `test_send_message_returns_false_for_invalid_token` (S2): call `send_message` with dummy token `"0000000000:INVALID"`, `_SMOKE_TG_CHAT_ID`, any text. Assert returns `False`, no exception raised.
- [x] 2.4 Implement `test_send_message_delivers_html_formatting` (S3): call `send_message` with `_SMOKE_TG_TOKEN`, `_SMOKE_TG_CHAT_ID`, body containing `<b>`, `<a href="...">`, `<code>` tags, prefixed `"🧪 auto-reddit smoke test — HTML"`. Assert returns `True`.

## Phase 3: Verification

- [x] 3.1 Run `uv run pytest tests/test_integration/test_operational.py -x --tb=short` without `TELEGRAM_SMOKE_*` vars — confirm all Telegram smoke tests are skipped and the suite passes.
- [x] 3.2 Run with `TELEGRAM_SMOKE_BOT_TOKEN` and `TELEGRAM_SMOKE_CHAT_ID` set to valid non-production credentials — confirm S1 and S3 pass (messages appear in the controlled chat) and S2 passes (returns `False`).  ✅ Re-run 2026-03-28: 3/3 passed after bot added to channel.
- [x] 3.3 Confirm existing `TestRedditSmokeOptional` behavior is unaffected — no imports changed, no shared state introduced.
