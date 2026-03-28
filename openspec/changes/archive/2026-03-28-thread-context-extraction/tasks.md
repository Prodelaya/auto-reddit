# Tasks: Thread Context Extraction

## Phase 1: Contracts & Foundation

- [x] 1.1 Add `ContextQuality` enum (`full`, `partial`, `degraded`) to `src/auto_reddit/shared/contracts.py`
- [x] 1.2 Add `RedditComment` model to `src/auto_reddit/shared/contracts.py` with fields: `comment_id`, `author`, `body`, `score`, `created_utc`, `permalink`, `parent_id`, `depth`, `source_api`
- [x] 1.3 Add `ThreadContext` model to `src/auto_reddit/shared/contracts.py` with fields: `candidate`, `comments`, `comment_count`, `quality`, `source_api`

## Phase 2: Core Implementation

- [x] 2.1 Create `src/auto_reddit/reddit/comments.py` with per-provider comment normalizers: `_normalize_comments_reddit34(raw) -> list[RedditComment]`, `_normalize_comments_reddit3(raw) -> list[RedditComment]`, `_normalize_comments_reddapi(raw) -> list[RedditComment]`
- [x] 2.2 Implement `_fetch_comments_reddit34(client, post_id, headers) -> tuple[list[RedditComment], ContextQuality]` using `_fetch_with_retry` from `reddit/client.py`. Assign quality `full`. Handle recursive `replies` tree flattening.
- [x] 2.3 Implement `_fetch_comments_reddit3(client, post_id, headers)` returning quality `partial`. Flatten tree recursively via `replies[]` to capture all comments, but leave `depth=None` and `parent_id=None` (raw payload has neither; nesting is NOT derived). Context is partial: ids and timestamps present, nesting metadata absent.
- [x] 2.4 Implement `_fetch_comments_reddapi(client, post_id, headers)` returning quality `degraded`. Flat list, no tree.
- [x] 2.5 Implement `_fetch_thread_context(candidate, api_key) -> ThreadContext | None` with fallback chain reddit34→reddit3→reddapi. Return `None` on total failure.

## Phase 3: Integration

- [x] 3.1 Implement public `fetch_thread_contexts(candidates: list[RedditCandidate], settings: Settings) -> list[ThreadContext]`. Iterate candidates, call `_fetch_thread_context`, drop `None` results, log drops.
- [x] 3.2 Wire `fetch_thread_contexts` into `src/auto_reddit/main.py`: replace the Change 3 placeholder comment with the actual call between `review_set` cut and Change 4 placeholder.

## Phase 4: Testing

- [x] 4.1 Create `tests/test_reddit/test_comments.py`. Test each normalizer with fixture payloads matching provider snapshots from design doc (reddit34 tree, reddit3 flat+nesting, reddapi flat).
- [x] 4.2 Test fallback chain: mock reddit34 failure → reddit3 success → verify quality `partial`. Mock all-fail → verify `None` return (post dropped).
- [x] 4.3 Test `fetch_thread_contexts`: given 3 candidates where 1 has total failure, verify output has 2 `ThreadContext` items and dropped post is logged.
- [x] 4.4 Test degradation indicator: verify `ContextQuality` is `full`/`partial`/`degraded` per provider source.
- [x] 4.5 Run full suite: `uv run pytest tests/ -x --tb=short` — all green.
