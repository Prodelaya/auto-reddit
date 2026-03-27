# Tasks: Reddit Candidate Collection

## Phase 1: Foundation (contracts + settings fix)

- [ ] 1.1 Add `RedditCandidate` Pydantic model to `src/auto_reddit/shared/contracts.py` with exact fields from design (`post_id`, `title`, `selftext`, `url`, `permalink`, `author`, `subreddit`, `created_utc`, `num_comments`, `source_api`) and `is_complete` computed field. Verify: import + instantiate with full/partial data.
- [ ] 1.2 Update `src/auto_reddit/config/settings.py`: change `max_daily_opportunities` and `daily_review_limit` defaults from 10 to 8. Verify: `Settings()` reflects new defaults.

## Phase 2: Core — per-provider normalizers

- [ ] 2.1 Create `_normalize_reddit3(raw_json: dict) -> list[RedditCandidate]` in `src/auto_reddit/reddit/client.py`. Map flat shape from reddit3 raws. Prefix relative permalinks with `https://www.reddit.com`. Set `source_api="reddit3"`.
- [ ] 2.2 Create `_normalize_reddit34(raw_json: dict) -> list[RedditCandidate]`. Navigate `data.posts[].data` nesting per reddit34 raws. Strip `t1_` prefix from IDs if present. Set `source_api="reddit34"`.
- [ ] 2.3 Create `_normalize_reddapi(raw_json: dict) -> list[RedditCandidate]`. Navigate `posts[].data` nesting per reddapi raws. Hardcode `User-Agent: RapidAPI Playground` header in the reddapi request path. Set `source_api="reddapi"`.

## Phase 3: Core — pagination, fallback, and collection orchestrator

- [ ] 3.1 Implement cursor-based pagination loop as a helper: fetch pages until oldest post in page is outside 7-day window OR no cursor returned. Parameterize by provider-specific URL builder and normalizer.
- [ ] 3.2 Implement `collect_candidates(settings) -> list[RedditCandidate]` with whole-step fallback chain: `reddit3 → reddit34 → reddapi`. First successful provider wins. On all-fail: log error, return `[]`. Apply 7-day `created_utc` filter and sort descending by `created_utc` after normalization.
- [ ] 3.3 Add retry logic per api-strategy §7: max 2 retries, backoff 2s→4s per call. Failure after retries triggers next provider in chain.

## Phase 4: Integration wiring

- [ ] 4.1 Wire `collect_candidates(settings)` call in `src/auto_reddit/main.py`. Pass returned `list[RedditCandidate]` as input to next pipeline step (placeholder for change 2). Verify: `main.py` imports and calls `collect_candidates`.

## Phase 5: Test fixtures + unit tests

- [ ] 5.1 Create `tests/test_reddit/conftest.py` with pytest fixtures loading sanitized JSON snapshots from `docs/integrations/reddit/{reddit3,reddit34,reddapi}/raw/` (posts endpoints only).
- [ ] 5.2 Create `tests/test_reddit/test_client.py` with tests: (a) each `_normalize_*` adapter produces valid `RedditCandidate` from fixture, (b) `is_complete` returns `True` for full posts and `False` when `selftext` or `author` is `None`.
- [ ] 5.3 Add tests for 7-day filter: mock `datetime.now`, verify boundary posts (exactly 7 days ago = included, 7d+1s = excluded).
- [ ] 5.4 Add tests for cursor pagination: mock API returning 2 pages + stop condition (no cursor / out-of-window), verify all posts collected.
- [ ] 5.5 Add tests for fallback chain: (a) reddit3 fail → reddit34 success, (b) all fail → empty list.
- [ ] 5.6 Add integration test for full `collect_candidates`: mock HTTP layer, verify end-to-end from call to sorted `list[RedditCandidate]` with no downstream rules applied.
