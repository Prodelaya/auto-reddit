# Design: Thread Context Extraction

## Technical Approach

Insert a `fetch_thread_contexts()` step in `main.py` between the daily review-set cut and the pending AI evaluation. This step lives in the existing `reddit/` module (it fetches from the same RapidAPI providers), receives `list[RedditCandidate]` from upstream, and returns `list[ThreadContext]` — a new Pydantic contract in `shared/contracts.py`. A per-post fallback chain (reddit34 -> reddit3 -> reddapi) fetches comments, normalizes them to `list[RedditComment]`, attaches a `ContextQuality` degradation indicator, and drops any post where all providers fail.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Module placement | Extend `reddit/` (new `reddit/comments.py`) | Separate `context/` module | Same provider credentials, same httpx patterns, same retry logic. Keeps module count lean per python-conventions skill. |
| Fallback chain per post | reddit34 -> reddit3 -> reddapi | Single provider; parallel calls | Matches api-strategy.md comment priority. Sequential saves quota; parallel would double/triple consumption. |
| Degradation indicator | `ContextQuality` enum: `full`, `partial`, `degraded`, `none` | Boolean flag; numeric score | `full` = reddit34 (tree+timestamps, full nesting metadata), `partial` = reddit3 (flattened list, timestamps+ids present, but no `depth`/`parent_id` — nesting metadata absent), `degraded` = reddapi (top comments only, no ids/timestamps/tree). Enum is simple, extensible, unambiguous. |
| Comment contract | `RedditComment` Pydantic model with nullable fields | Dict/untyped | Reuses the shape already proposed in api-strategy.md. Nullable fields tolerate reddapi gaps without separate model. |
| Drop vs emit on total failure | Drop post from batch | Emit with quality=none | Spec says MUST drop. Avoids misleading downstream with empty context payloads. |
| Reuse existing `_fetch_with_retry` | Yes, import from `reddit/client.py` | Copy or new retry util | DRY. Same retry policy (2 retries, 2s/4s backoff) applies to comment fetches. Refactor to module-level private if needed. |

## Data Flow

```
main.py review_set (list[RedditCandidate], max 8)
    |
    v
reddit/comments.py :: fetch_thread_contexts(candidates, settings)
    |
    +-- for each candidate:
    |     |
    |     +-- _fetch_comments_reddit34(post_url, api_key)
    |     |     success? -> normalize -> quality=full
    |     |     fail? ↓
    |     +-- _fetch_comments_reddit3(post_url, api_key)
    |     |     success? -> normalize -> quality=partial
    |     |     fail? ↓
    |     +-- _fetch_comments_reddapi(post_url, api_key)
    |     |     success? -> normalize -> quality=degraded
    |     |     fail? -> drop post, log warning
    |     |
    |     +-- build ThreadContext(candidate, comments, quality)
    |
    v
list[ThreadContext] (0..N, N <= len(review_set))
    |
    v
(future) change 4: ai-opportunity-evaluation
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/shared/contracts.py` | Modify | Add `ContextQuality` enum, `RedditComment` model, `ThreadContext` model. |
| `src/auto_reddit/reddit/comments.py` | Create | Per-post comment fetching with fallback chain, per-provider normalizers, and `fetch_thread_contexts()` public entry point. |
| `src/auto_reddit/reddit/__init__.py` | Modify | Re-export `fetch_thread_contexts` if needed. |
| `src/auto_reddit/main.py` | Modify | Wire `fetch_thread_contexts(review_set, settings)` replacing the change-3 placeholder comment. |
| `tests/test_reddit/test_comments.py` | Create | Unit tests for normalizers, fallback chain, drop-on-total-failure, quality assignment. |

## Interfaces / Contracts

```python
class ContextQuality(str, Enum):
    full = "full"           # reddit34: tree, timestamps, ids, permalinks
    partial = "partial"     # reddit3: flattened list, timestamps+ids present, no depth/parent_id, no order guarantee
    degraded = "degraded"   # reddapi: top comments only, no ids/timestamps/tree

class RedditComment(BaseModel):
    comment_id: str | None = None       # None for reddapi
    author: str | None = None
    body: str                           # normalized from text/content/comment
    score: int | None = None
    created_utc: int | None = None      # None for reddapi
    permalink: str | None = None        # full URL or None
    parent_id: str | None = None        # without t1_ prefix; None if top-level, reddit3, or reddapi
    depth: int | None = None            # None for reddit3 and reddapi (only reddit34 provides it)
    source_api: str

class ThreadContext(BaseModel):
    candidate: RedditCandidate          # original upstream post
    comments: list[RedditComment]       # normalized, may be empty if all comments had empty body
    comment_count: int                  # len(comments) at normalization time
    quality: ContextQuality             # degradation indicator
    source_api: str                     # which provider succeeded
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Per-provider normalizers produce correct `RedditComment` list from raw snapshots | Load raw JSON fixtures from `docs/integrations/reddit/*/raw/`, assert field mapping and nullable handling. |
| Unit | `ContextQuality` assignment per provider | Assert reddit34->full, reddit3->partial, reddapi->degraded. |
| Unit | Fallback chain: first success wins, total failure drops post | Mock `_fetch_with_retry` to raise for N providers, verify correct quality or exclusion. |
| Unit | `ThreadContext` preserves original `RedditCandidate` unchanged | Assert `candidate` pass-through identity. |
| Integration | `fetch_thread_contexts` end-to-end with mocked HTTP | `respx` or `pytest-httpx` to mock httpx calls, verify full pipeline. |

## Provider Raw Review & Recommendations

Based on verified snapshots (2026-03-27):

### reddit34 (`getPostCommentsWithSort?sort=new`)
- **Top-level comments**: All present, sorted by recency descending. Verified.
- **Replies**: Nested recursively with `depth`, `parent_id` (prefixed `t1_`), `permalink`, `created` (ISO 8601), `score`. Tree is complete for the sample.
- **Caveat**: At least one comment (`t1_ocoqaq4`) returned `text: ""` despite having content in other providers. Pipeline MUST tolerate empty text without discarding the comment.
- **Recommendation**: Flatten tree recursively, strip `t1_` prefix from ids. Parse ISO `created` to unix timestamp. This is the best source — mark as `quality=full`.

### reddit3 (`/v1/reddit/post?url=...`)
- **Top-level comments**: Present under `body.post_comments[]`. Fields: `id` (no prefix), `author`, `content`, `up_votes`/`score`, `created_utc` (unix), `replies[]`.
- **Replies**: Nested under `replies[]` with same shape. Tree verified to depth 3.
- **Caveat**: Comment order is NOT guaranteed chronological — appears to be Reddit's default sort (best/hot). If downstream needs recency, client must sort by `created_utc`.
- **Caveat**: No `parent_id` or `depth` fields in the raw payload. Nesting position in the recursive tree is NOT used to derive these fields — `depth=None` and `parent_id=None` for all reddit3 comments. Downstream AI must operate without nesting metadata when context quality is `partial`.
- **Recommendation**: Flatten tree recursively (traverse `replies[]` to capture all comments). Do NOT derive `depth` or `parent_id`. Mark as `quality=partial` because order is unreliable and nesting metadata is absent.

### reddapi (`/api/scrape_post_comments` and `/api/scrape_new_comments_and_its_post_content`)
- **Comments**: Flat list under `comments[]` or `data.top comments[]`. Fields: `comment` (body), `author`, `user_id`, `score`. That's it.
- **Missing**: No `comment_id`, no `created`/timestamp, no `permalink`, no `parent_id`, no `depth`, no replies. Label says "top comments" — not sorted by recency.
- **Recommendation**: Normalize `comment` -> `body`. Leave all temporal/structural fields as None. Mark as `quality=degraded`. Prefer `/api/scrape_post_comments` (simpler, comments-only) over the combined endpoint.

### Cross-Provider Summary

| Field | reddit34 | reddit3 | reddapi |
|-------|----------|---------|---------|
| comment_id | Yes (t1_ prefix) | Yes (no prefix) | No |
| author | Yes | Yes | Yes |
| body/text | Yes (occasional empty) | Yes (`content`) | Yes (`comment`) |
| score | Yes | Yes | Yes |
| created | Yes (ISO 8601) | Yes (unix) | No |
| permalink | Yes (full) | No | No |
| parent_id | Yes (t1_ prefix) | No (always None) | No |
| depth | Yes (explicit) | No (always None) | No |
| replies/tree | Yes (recursive) | Yes (recursive) | No (flat) |
| Sort guarantee | Yes (sort=new) | No (default sort) | No ("top") |

## Migration / Rollout

No migration required. The change adds a new pipeline step that replaces a placeholder comment in `main.py`. The `ThreadContext` model is new and has no stored state. Downstream changes (4, 5) will consume the output but are not yet implemented.

## Open Questions

- None blocking. All provider shapes are verified from raw snapshots.
