# Tasks: Operational Integration Tests

## Phase 1: Infrastructure

- [x] 1.1 Create `tests/test_integration/__init__.py` (empty package marker)
- [x] 1.2 Create `tests/test_integration/test_operational.py` with imports: `pytest`, `unittest.mock`, `os`, `time`, `auto_reddit.main.run`, `auto_reddit.shared.contracts` (RedditCandidate, AcceptedOpportunity, OpportunityType, ThreadContext), `auto_reddit.persistence.store.CandidateStore`
- [x] 1.3 Add shared helpers following existing `test_deliver_daily.py` pattern: `_make_opportunity_json(post_id)`, `_make_settings(tmp_path, cap=8)` returning mock Settings with `db_path=str(tmp_path/"test.db")` and dummy tokens, `_make_candidate(post_id, created_utc)`, `_make_thread_context(candidate)`
- [x] 1.4 Add `@pytest.fixture` `operational_store(tmp_path)` returning initialized `CandidateStore(str(tmp_path/"test.db"))` with `init_db()` called

## Phase 2: Core Tests (Spec Scenarios P1-P3)

- [x] 2.1 **P1 — Retry without AI re-evaluation**: Insert `pending_delivery` record with valid `opportunity_data` into real store. Patch `auto_reddit.main.evaluate_batch` as failing sentinel. Patch other 4 boundaries. Call `main.run()`. Assert delivery succeeds from persisted data AND `evaluate_batch` sentinel was NOT called. Patch `time.time` to fixed epoch.
- [x] 2.2 **P2 — Delivery boundary isolation**: Pre-insert `pending_delivery` records into real store. Patch `auto_reddit.main.collect_candidates`, `fetch_thread_contexts`, `evaluate_batch` to return empty/controlled results (empty-input traversal is expected — `main.run()` always calls these; the proof is that they have no side effect, not that they are never invoked). Patch `auto_reddit.delivery.send_message` returning True. Call `main.run()`. Assert delivery reads only the pre-inserted persisted set and that upstream boundaries produced no collection, extraction, evaluation, or publishing output beyond the controlled empty-input pass.
- [x] 2.3 **P3 — Evaluation boundary isolation**: Patch `auto_reddit.main.collect_candidates` returning controlled candidates. Patch `fetch_thread_contexts` returning controlled contexts. Let `evaluate_batch` return controlled result. Patch `auto_reddit.delivery.send_message` as strict sentinel (raises if called) with `RejectedPost` result — proves evaluation does not produce Telegram side effects. Secondary test: `AcceptedOpportunity` result persisted to store before downstream delivery phase. Assert evaluation returns bounded outcome; delivery is a separate downstream phase, not an eval side effect.

## Phase 3: Multi-Run Memory Test (Spec Scenario P4)

- [x] 3.1 **P4 — Run 1**: Patch all 5 I/O boundaries with controlled data. `evaluate_batch` returns 1 accepted + 1 rejected. `send_message` returns True. Call `main.run()`. Assert store has 1 `sent`, 1 `rejected`.
- [x] 3.2 **P4 — Run 2**: Same `tmp_path` db, fresh patches. `collect_candidates` returns same post_ids + 1 new. Assert `sent`/`rejected` excluded from review. New post processed. Insert `pending_delivery` manually before run 2 with sentinel `evaluate_batch`. Verify retry reads persisted `opportunity_data` without AI call.

## Phase 4: Smoke Tests + Final Validation

- [x] 4.1 Add `@pytest.mark.skipif(not os.getenv("REDDIT_SMOKE_API_KEY"))` smoke test class. Verify real Reddit API returns non-empty candidates. Non-blocking, skipped by default.
- [x] 4.2 Run `uv run pytest tests/ -x --tb=short` — 269 passed, 1 skipped. No regressions.
