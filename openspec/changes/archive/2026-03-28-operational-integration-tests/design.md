# Design: Operational Integration Tests

## Technical Approach

Exercise the real `main.run()` orchestration path against a real SQLite database (`tmp_path`), patching only the five external I/O boundaries (`collect_candidates`, `fetch_thread_contexts`, `evaluate_batch`, `send_message`, and `Settings`) at their import sites inside `auto_reddit.main`. No production code changes. Tests live in `tests/test_integration/test_operational.py`.

## Architecture Decisions

| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|
| 1 | Patch at `auto_reddit.main.*` caller namespace | Patch at source module | `main.py` imports symbols directly; patching at source misses the bound reference. Matches discovery risk §1. |
| 2 | Real `CandidateStore` + `tmp_path` SQLite | Mock store | Multi-run memory proof (P4) requires real SQL state across invocations. Mock would bypass the exact behavior under test. |
| 3 | Shared `_make_opportunity_json()` helper following existing `test_deliver_daily.py` pattern | Inline JSON | Repo convention; keeps fixture data consistent and DRY. |
| 4 | `@pytest.fixture` for store + settings instead of class-level setup | `unittest.TestCase` | Follows existing repo pattern (all 259 tests use pytest fixtures, no TestCase). |
| 5 | `pytest.mark.skipif(not os.getenv("REDDIT_SMOKE_API_KEY"))` for smoke tests | Settings-based flag / custom marker | Constraint: env-gated via `os.getenv`, not Settings. `skipif` is idiomatic pytest. |
| 6 | Deterministic `time.time` via `freezegun` or `mock.patch("time.time")` | Real clock | `selector._expiry_ts` and delivery retry/new classification depend on `time.time()`. Fixed timestamps eliminate flakiness. |
| 7 | Controlled-empty patch strategy for P2 (not hard-fail sentinels) | Patching upstream boundaries as raising sentinels + refactoring `main.run()` to skip phases | `main.run()` unconditionally traverses the full pipeline; making upstream boundaries hard-fail sentinels would require refactoring production code, which is out of scope. The accepted proof strategy patches them to return empty/controlled results so the traversal has zero side effect, then asserts delivery output comes only from the pre-inserted persisted set. |
| 8 | `python-dotenv` + `load_dotenv()` for smoke test env loading | Relying on pre-sourced shell env / pytest-dotenv plugin | `os.getenv()` does not read `.env` files; manual smoke runs would skip even with a valid `.env`. `python-dotenv` is already a transitive dep of `pydantic-settings`, so adding it to dev deps is zero-cost. |

## Data Flow

```
Test fixture
  │
  ├─ real CandidateStore(tmp_path / "test.db") ──► SQLite file
  │
  ├─ mock Settings (db_path=tmp_path, dummy tokens, cap=8)
  │
  └─ mock.patch boundaries at auto_reddit.main.*:
       ├─ collect_candidates  → returns controlled [RedditCandidate]
       ├─ fetch_thread_contexts → returns controlled [ThreadContext]
       ├─ evaluate_batch → returns controlled [AcceptedOpportunity|RejectedPost]
       │                     OR sentinel (for P1 retry proof)
        ├─ send_message (auto_reddit.delivery.send_message) → True
        └─ settings → mock Settings with tmp_path db_path

  main.run()  ← real orchestration, real store, patched I/O
       │
       └─► assertions on store state + mock call counts
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `tests/test_integration/__init__.py` | Create | Package marker (empty) |
| `tests/test_integration/test_operational.py` | Create | P1-P4 operational tests + optional smoke |

## Patch Points & Fixture Strategy

### Patch targets (all from `auto_reddit.main` namespace)

| Symbol | Patch path | Role in tests |
|--------|-----------|---------------|
| `collect_candidates` | `auto_reddit.main.collect_candidates` | Returns controlled `RedditCandidate` list |
| `fetch_thread_contexts` | `auto_reddit.main.fetch_thread_contexts` | Returns controlled `ThreadContext` list |
| `evaluate_batch` | `auto_reddit.main.evaluate_batch` | Returns results OR sentinel that fails if called |
| `settings` | `auto_reddit.main.settings` | Mock with `db_path` pointing to `tmp_path` SQLite |
| `send_message` | `auto_reddit.delivery.send_message` | Returns `True` (Telegram success) or sentinel. Note: `delivery/__init__.py` imports `send_message` from `.telegram` at module load; patching at `auto_reddit.delivery.send_message` (the caller namespace) is the effective target — patching at `auto_reddit.delivery.telegram.send_message` would NOT intercept calls already bound in `__init__.py`. |

### Fixtures

```python
@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "operational.db")

@pytest.fixture
def mock_settings(db_path):
    s = MagicMock()
    s.db_path = db_path
    s.daily_review_limit = 8
    s.max_daily_deliveries = 8
    s.telegram_bot_token = "TEST_TOKEN"
    s.telegram_chat_id = "TEST_CHAT"
    s.review_window_days = 7
    s.reddit_api_key = "FAKE"
    s.deepseek_api_key = "FAKE"
    s.deepseek_model = "test-model"
    return s
```

`_make_opportunity_json(post_id)` helper reuses the pattern from `tests/test_delivery/test_deliver_daily.py`.

## Multi-Run Orchestration (P4)

1. **Run 1**: Patch `evaluate_batch` to return 1 accepted + 1 rejected. Patch `send_message` → `True`. Call `main.run()`. Assert store has: 1 `sent`, 1 `rejected`.
2. **Run 2**: Same `db_path`, fresh patches. Patch `collect_candidates` to return the same post_ids plus a new one. Call `main.run()`. Assert: `sent`/`rejected` excluded from `eligible` (via `get_decided_post_ids()`), new post processed normally.
3. **Retry sub-case**: Before run 2, insert a `pending_delivery` manually. Patch `evaluate_batch` as sentinel. Verify delivery reads the persisted `opportunity_data` without calling `evaluate_batch`.

Both runs use the SAME `db_path` fixture value — `tmp_path` scoping ensures isolation between test functions but allows sequential runs within one test function.

## Smoke-Test Gating

```python
from dotenv import load_dotenv
load_dotenv()  # Ensure .env is loaded for manual/local runs.

REDDIT_SMOKE_KEY = os.getenv("REDDIT_SMOKE_API_KEY") or os.getenv("REDDIT_API_KEY")

@pytest.mark.skipif(not REDDIT_SMOKE_KEY, reason="Neither REDDIT_SMOKE_API_KEY nor REDDIT_API_KEY is set")
def test_reddit_api_smoke():
    """Live Reddit API connectivity check — skipped by default."""
```

`python-dotenv` is a dev dependency (already a transitive dep of `pydantic-settings`). The `load_dotenv()` call is placed before the env-gate module-level variable so `.env` values are available to `os.getenv()` during manual/local execution. No Settings involved. No `.env.example` change. Non-blocking: failure in smoke does not affect P1-P4 pass/fail.

## Flakiness Prevention

| Source | Mitigation |
|--------|-----------|
| `time.time()` in store/selector | Patch `time.time` to return fixed epoch in all operational tests |
| Delivery retry vs new classification | Fixed `decided_at` timestamps well before "today" boundary |
| SQLite WAL locking | Single-threaded pytest; `tmp_path` per-test isolation |
| Import-time `Settings()` validation | Patch `auto_reddit.main.settings` BEFORE calling `run()` |
| `logging.basicConfig` re-entry | Harmless in tests; no mitigation needed |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| P1 (retry reuse) | `pending_delivery` reuses `opportunity_data`, skips AI | Sentinel `evaluate_batch` + real store |
| P2 (delivery boundary) | Delivery reads only pending set; upstream phases traverse with empty/controlled input — no collection, extraction, AI evaluation, or publishing side effect | Controlled-empty patches on `collect_candidates`/`fetch_thread_contexts`/`evaluate_batch`; `main.run()` always calls these, so the proof is zero side-effect output, not zero invocations |
| P3 (evaluation boundary) | Evaluation consumes only thread context, no delivery/Reddit side effects | Sentinel patches on collect/deliver |
| P4 (memory exclusion) | Multi-run: sent/rejected excluded, pending retryable | Two sequential `main.run()` calls, same SQLite |
| Smoke (optional) | Reddit API reachable | `skipif` env-gate, live HTTP call |

## Migration / Rollout

No migration required. New test files only; production code untouched.

## Open Questions

None. All decisions closed in discovery and spec phases.
