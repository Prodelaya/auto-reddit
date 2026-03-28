# Tasks: Telegram Daily Delivery

## Phase 1: Foundation (config + contracts)

- [x] 1.1 Add `max_daily_deliveries: int = 8` to `Settings` in `src/auto_reddit/config/settings.py` (rename or alias existing `max_daily_opportunities` if redundant). Verify `.env.example` documents the new field.
- [x] 1.2 Create `DeliveryReport` Pydantic model in `src/auto_reddit/shared/contracts.py` with fields: `total_selected`, `retries`, `new`, `sent_ok`, `sent_failed`, `summary_sent: bool`, `expired_skipped`.

## Phase 2: Core Implementation

- [x] 2.1 Create `src/auto_reddit/delivery/selector.py` — pure function `select_deliveries(records: list[PostRecord], now: int, cap: int = 8) -> list[PostRecord]`. Must: filter expired via TTL rule (Mon-Wed→Fri 23:59, Thu-Fri→next Mon 23:59, Sat-Sun→next Mon), sort retries by `decided_at` ASC first, fill remaining cap with new unsent records by `decided_at` ASC.
- [x] 2.2 Create `src/auto_reddit/delivery/renderer.py` — pure functions `render_opportunity(opp: AcceptedOpportunity) -> str` (deterministic HTML from persisted fields: title, link, type, reason, summaries, suggested responses, warning/bullets if present) and `render_summary(count: int, retry_count: int, new_count: int, *, date, reviewed_post_count) -> str` (HTML summary with date + reviewed count per product.md §10).
- [x] 2.3 Implement `send_message(token: str, chat_id: str, text: str) -> bool` in `src/auto_reddit/delivery/telegram.py` — POST to `https://api.telegram.org/bot{token}/sendMessage` with `parse_mode=HTML`, return `True` only when HTTP 200 and `ok=true` in response body. Use httpx sync.
- [x] 2.4 Create `deliver_daily(store: CandidateStore, settings: Settings, *, reviewed_post_count, run_date) -> DeliveryReport` façade in `src/auto_reddit/delivery/__init__.py`. Flow: `store.get_pending_deliveries()` → `select_deliveries()` → `render_summary()` + `send_message()` (log failure, don't block) → for each record: `model_validate_json(opportunity_data)` → `render_opportunity()` → `send_message()` → if True: `store.mark_sent()`, else log+skip. Return `DeliveryReport`.

## Phase 3: Integration

- [x] 3.1 Wire `deliver_daily(store, settings, reviewed_post_count=len(review_set))` in `src/auto_reddit/main.py`.

## Phase 4: Testing

- [x] 4.1 Create `tests/test_delivery/test_selector.py` — test TTL expiry for each weekday bucket (Mon-Wed→Fri, Thu-Fri→Mon, Sat-Sun→Mon), retry-first ordering, cap enforcement, mixed retry+new fill. Scenario coverage: "Retry backlog consumes cap first", "Remaining capacity filled with new".
- [x] 4.2 Create `tests/test_delivery/test_renderer.py` — test `render_opportunity()` produces valid HTML from a fixture `AcceptedOpportunity` (with and without warning/bullets), test `render_summary()` output format.
- [x] 4.3 Create `tests/test_delivery/test_telegram.py` — test `send_message()` with mocked httpx: success (200 + ok=true → True), failure (non-200 → False), malformed JSON → False. Verify `parse_mode=HTML` in request.
- [x] 4.4 Create `tests/test_delivery/test_deliver_daily.py` — integration test for façade: mock `store` + `send_message`, verify summary sent first (non-blocking on failure), `mark_sent` called only on success, `DeliveryReport` counts correct. Scenario: "Summary failure does not stop opportunity delivery".
- [x] 4.5 Add TTL edge-case test in `test_selector.py`: record exactly at expiry boundary (Friday 23:59:59 vs Saturday 00:00:00), defensive Sat/Sun handling.

## Phase 5: Cleanup

- [x] 5.1 Update `src/auto_reddit/delivery/__init__.py` exports to expose `deliver_daily` as the public API.
- [x] 5.2 Verify `uv run pytest tests/ -x --tb=short` passes with all new and existing tests.

## Phase 6: Corrective Apply (post-verify fixes)

- [x] C.1 Fix delivery boundary: `selector.py` validates `opportunity_data` as valid `AcceptedOpportunity` JSON before selecting records — malformed JSON excluded before cap, not after.
- [x] C.2 Align summary with `product.md §10`: `render_summary()` now accepts `date` and `reviewed_post_count` kwargs; `deliver_daily()` accepts `reviewed_post_count` and `run_date`; `main.py` passes `reviewed_post_count=len(review_set)`.
- [x] C.3 Add `purge_expired(post_ids)` helper to `persistence/store.py` (optional, per design).
- [x] C.4 Add corrective tests: `TestMalformedOpportunityDataExclusion` in `test_selector.py` (5 tests), `TestRenderSummaryProductAlignment` in `test_renderer.py` (6 tests), `TestDeliverDailyReviewedPostCount` in `test_deliver_daily.py` (3 tests). Update `TestInvalidOpportunityData` to match corrected boundary semantics.

## Status: ALL TASKS COMPLETE — 259/259 tests pass
