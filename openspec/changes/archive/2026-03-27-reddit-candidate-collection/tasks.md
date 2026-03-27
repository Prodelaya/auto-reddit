# Tasks: Reddit Candidate Collection

## Phase 1: Foundation (contracts + settings fix)

- [x] 1.1 Add `RedditCandidate` Pydantic model to `src/auto_reddit/shared/contracts.py` with exact fields from design (`post_id`, `title`, `selftext`, `url`, `permalink`, `author`, `subreddit`, `created_utc`, `num_comments`, `source_api`) and `is_complete` computed field. Verify: import + instantiate with full/partial data.
- [x] 1.2 Update `src/auto_reddit/config/settings.py`: change `max_daily_opportunities` and `daily_review_limit` defaults from 10 to 8. Verify: `Settings()` reflects new defaults. **NOTE: already correct at 8 in settings.py — no change needed.**

## Phase 2: Core — per-provider normalizers

- [x] 2.1 Create `_normalize_reddit3(raw_json: dict) -> list[RedditCandidate]` in `src/auto_reddit/reddit/client.py`. Map flat shape from reddit3 raws. Prefix relative permalinks with `https://www.reddit.com`. Set `source_api="reddit3"`.
- [x] 2.2 Create `_normalize_reddit34(raw_json: dict) -> list[RedditCandidate]`. Navigate `data.posts[].data` nesting per reddit34 raws. Strip `t1_` prefix from IDs if present. Set `source_api="reddit34"`.
- [x] 2.3 Create `_normalize_reddapi(raw_json: dict) -> list[RedditCandidate]`. Navigate `posts[].data` nesting per reddapi raws. Hardcode `User-Agent: RapidAPI Playground` header in the reddapi request path. Set `source_api="reddapi"`.

## Phase 3: Core — pagination, fallback, and collection orchestrator

- [x] 3.1 Implement cursor-based pagination loop as a helper: fetch pages until oldest post in page is outside 7-day window OR no cursor returned. Parameterize by provider-specific URL builder and normalizer.
- [x] 3.2 Implement `collect_candidates(settings) -> list[RedditCandidate]` with whole-step fallback chain: `reddit3 → reddit34 → reddapi`. First successful provider wins. On all-fail: log error, return `[]`. Apply 7-day `created_utc` filter and sort descending by `created_utc` after normalization.
- [x] 3.3 Add retry logic per api-strategy §7: max 2 retries, backoff 2s→4s per call. Failure after retries triggers next provider in chain.

## Phase 4: Integration wiring

- [x] 4.1 Wire `collect_candidates(settings)` call in `src/auto_reddit/main.py`. Pass returned `list[RedditCandidate]` as input to next pipeline step (placeholder for change 2). Verify: `main.py` imports and calls `collect_candidates`.

## Phase 5: Test fixtures + unit tests

- [x] 5.1 Create `tests/test_reddit/conftest.py` with pytest fixtures loading sanitized JSON snapshots from `docs/integrations/reddit/{reddit3,reddit34,reddapi}/raw/` (posts endpoints only).
- [x] 5.2 Create `tests/test_reddit/test_client.py` with tests: (a) each `_normalize_*` adapter produces valid `RedditCandidate` from fixture, (b) `is_complete` returns `True` for full posts and `False` when `selftext` or `author` is `None`.
- [x] 5.3 Add tests for 7-day filter: mock `datetime.now`, verify boundary posts (exactly 7 days ago = included, 7d+1s = excluded).
- [x] 5.4 Add tests for cursor pagination: mock API returning 2 pages + stop condition (no cursor / out-of-window), verify all posts collected.
- [x] 5.5 Add tests for fallback chain: (a) reddit3 fail → reddit34 success, (b) all fail → empty list.
- [x] 5.6 Add integration test for full `collect_candidates`: mock HTTP layer, verify end-to-end from call to sorted `list[RedditCandidate]` with no downstream rules applied.

## Phase 6: Correctivos post-verify (cerrar gaps críticos y warnings)

- [x] 6.1 `is_complete` cubre TODO el contrato mínimo: `post_id`, `title`, `url`, `permalink`, `subreddit`, `created_utc` (non-zero), `source_api`, `selftext` (not None), `author` (not None). `num_comments` sigue siendo opcional y no afecta completeness.
- [x] 6.2 Normalizers usan `.get("id", "")` en vez de `item["id"]` — posts sin `id` se conservan con `post_id=""` → `is_complete=False`, sin lanzar excepción.
- [x] 6.3 `collect_candidates()` aplica filtro explícito `subreddit.lower() == "odoo"` tras normalizar, evitando ruido de otros subreddits.
- [x] 6.4 Helper `_to_absolute_url()` extraído; todos los normalizers canonican tanto `url` como `permalink` a URL absoluta (Opción A acordada por usuario).
- [x] 6.5 Test runtime `TestNoTruncationAboveEight`: 12 posts dentro de la ventana → 12 entregados, >8 garantizado sin truncación (cierra escenario spec).
- [x] 6.6 Tests `TestRetryBackoff`: 4 tests cubren retry/backoff de `_fetch_with_retry` (éxito en 2º intento, 3º intento, todos fallan, éxito en 1º).
