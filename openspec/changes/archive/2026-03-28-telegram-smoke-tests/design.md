# Design: Telegram Smoke Tests

## Technical Approach

Extend the existing env-gated smoke pattern (`TestRedditSmokeOptional` at line 812 of `test_operational.py`) with a parallel `TestTelegramSmokeOptional` class in the same file. Tests call `send_message()` directly from `auto_reddit.delivery.telegram`, gated by dedicated `TELEGRAM_SMOKE_*` env vars. No production code is modified.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|----------|--------|------------------------|-----------|
| File placement | Same `tests/test_integration/test_operational.py` | New file `test_telegram_smoke.py` | Follows established Reddit smoke pattern; one operational smoke section per integration boundary. Config rule: keep smoke within operational test boundaries. |
| Env var naming | `TELEGRAM_SMOKE_BOT_TOKEN`, `TELEGRAM_SMOKE_CHAT_ID` | Reuse production `TELEGRAM_BOT_TOKEN` | Spec scenario 3 explicitly forbids production credentials as the activation contract. Dedicated `SMOKE_` prefix guarantees isolation. |
| Env loading | `os.getenv()` at module level after existing `load_dotenv()` | Inject via `Settings` model | Reddit smoke uses raw `os.getenv()` (line 805). Settings model owns production config, smoke stays outside it — no production code changes. |
| Gating mechanism | Single `pytest.mark.skipif` on the class | Per-test skipif, custom marker | Matches `TestRedditSmokeOptional` exactly (line 808). Both vars required — either missing skips all Telegram smoke tests. |
| Invalid-token test (S2) | Inside `TestTelegramSmokeOptional`, guarded by same skipif | Always-run test in separate class | Discovery noted S2 could run without env vars, but the spec scopes all Telegram smoke under the same gating contract. Keeping S2 inside the gated class avoids accidental real API calls during standard runs. |
| Smoke message content | Prefixed with `🧪 auto-reddit smoke test` | Generic text | Discovery AC requires identifiable messages. Prefix distinguishes smoke from production delivery in the controlled chat. |
| Settings compatibility | Add `extra="ignore"` to `Settings.model_config` | Filter env vars before pydantic-settings | pydantic-settings v2 defaults to `extra="forbid"`, so any smoke-only var (e.g. `REDDIT_SMOKE_API_KEY`) in `.env` crashes Settings at import time. `extra="ignore"` lets Settings skip unknown vars while smoke tests read them via raw `os.getenv()`. |

## Data Flow

```
Developer sets TELEGRAM_SMOKE_* env vars
        │
        ▼
load_dotenv() ──→ os.getenv("TELEGRAM_SMOKE_BOT_TOKEN")
                  os.getenv("TELEGRAM_SMOKE_CHAT_ID")
        │
        ▼
pytest.mark.skipif (both present? → run)
        │
        ▼
send_message(token, chat_id, text) ──→ Telegram API
        │                                    │
        ▼                                    ▼
assert True/False              controlled non-prod chat
```

No store, no pipeline, no AI — smoke tests touch only the `send_message()` boundary.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `tests/test_integration/test_operational.py` | Modify | Append `TestTelegramSmokeOptional` class with 3 test methods (S1, S2, S3) after existing `TestRedditSmokeOptional`. Add `_SMOKE_TG_TOKEN` / `_SMOKE_TG_CHAT_ID` module-level vars. |
| `src/auto_reddit/config/settings.py` | Modify | Add `"extra": "ignore"` to `model_config` so smoke-only env vars don't crash pydantic-settings at import time. |

## Interfaces / Contracts

No new interfaces. Tests consume the existing public API:

```python
# Existing — no changes
def send_message(token: str, chat_id: str, text: str) -> bool: ...
```

Smoke env contract (read-only, not added to Settings or `.env.example`):

| Variable | Purpose | Required for smoke |
|----------|---------|-------------------|
| `TELEGRAM_SMOKE_BOT_TOKEN` | Bot token for controlled test chat | Yes (both) |
| `TELEGRAM_SMOKE_CHAT_ID` | Chat/channel ID for controlled test chat | Yes (both) |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Smoke (S1) | `send_message()` succeeds with valid smoke credentials | Call with plain text, assert `True` |
| Smoke (S2) | `send_message()` returns `False` with invalid token | Call with dummy token `"0000000000:INVALID"`, assert `False`, no exception |
| Smoke (S3) | `send_message()` delivers HTML formatting correctly | Call with `<b>`, `<a>`, `<code>` tags, assert `True` |

All three are env-gated, non-blocking, and do not affect the existing 269+ tests.

## Migration / Rollout

No migration required. Rollback: remove the `TestTelegramSmokeOptional` class and its module-level variables.

## Open Questions

None — all decisions closed in discovery and spec phases.
