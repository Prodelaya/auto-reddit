# Design: Reddit Candidate Collection

## Technical Approach

A `collect_candidates()` function in `reddit/client.py` orchestrates a fallback chain (`reddit3 → reddit34 → reddapi`) to fetch ALL posts from `r/Odoo`, filters by `created_utc` within 7 days, normalizes each post to a shared Pydantic contract in `shared/contracts.py`, marks incomplete posts explicitly, and returns the full sorted list in memory. No downstream rules (cut to 8, memory exclusion, comments) are applied. `main.py` calls this function and passes the result to the next pipeline step.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Fallback granularity | **Whole-step failover**: if reddit3 fails entirely, try reddit34, then reddapi. First successful provider wins. | Per-page failover (switch mid-pagination) | Simpler, avoids deduplication across providers. A provider that returns page 1 will almost certainly return page 2. Per-page failover is premature complexity. |
| Pagination strategy | **Cursor-based exhaustion with 7-day guard**: keep fetching pages via `cursor` until the oldest post in a page falls outside the 7-day window or no cursor is returned. | Fixed single call; time-based binary search | All 3 APIs return ~25 posts and a `cursor`. `r/Odoo` averages ~3-5 posts/day → ~25 posts/week fits in 1 call most weeks. The loop handles growth without code changes. Budget: 1-2 req/day for posts. |
| Incomplete post handling | **Optional fields in Pydantic model** with a computed `is_complete` property | Separate `IncompletePost` type; discard-and-log | Single type simplifies downstream consumption. `is_complete` is derivable, not stored. |
| Normalization location | **Per-provider adapter functions** (`_normalize_reddit3`, `_normalize_reddit34`, `_normalize_reddapi`) inside `reddit/client.py` | Generic dict-mapping config | Each provider has a different nesting depth and field-name variance (raws confirm: reddit3 flat, reddit34 `data.posts[].data`, reddapi `posts[].data`). Explicit adapters are safer and testable. |
| `reddapi` User-Agent | **Hardcode `User-Agent: RapidAPI Playground`** in the reddapi adapter only | Config param; omit and accept 403 | Raw evidence proves 403→200 flip depends solely on this header. No reason to make it configurable yet. |
| Settings defaults | **Update `max_daily_opportunities` and `daily_review_limit` defaults to 8** in `settings.py` | Leave at 10 | product.md and api-strategy.md both mandate 8 as the operative reference. Settings correction is a prerequisite fix. |

## Data Flow

```
main.py
  │
  ▼
collect_candidates(settings) ─── reddit/client.py
  │
  ├─ try reddit3: GET /v1/reddit/posts?url=...&filter=new [+cursor loop]
  │    └─ _normalize_reddit3(raw) → list[RedditCandidate]
  │
  ├─ (on fail) try reddit34: GET /getPostsBySubreddit?subreddit=odoo&sort=new [+cursor loop]
  │    └─ _normalize_reddit34(raw) → list[RedditCandidate]
  │
  ├─ (on fail) try reddapi: GET /api/scrape/new?subreddit=odoo&limit=25 [+cursor loop]
  │    └─ _normalize_reddapi(raw) → list[RedditCandidate]
  │
  ├─ (all fail) ABORT: log error, return empty list
  │
  ▼
  filter: created_utc ≥ (now - 7 days)
  sort: descending by created_utc
  return: list[RedditCandidate]   ──→  main.py passes to next step (change 2)
```

## Interfaces / Contracts

```python
# shared/contracts.py
from pydantic import BaseModel, computed_field
from datetime import datetime

class RedditCandidate(BaseModel):
    post_id: str
    title: str
    selftext: str | None = None
    url: str                          # always full URL
    permalink: str                    # always full URL
    author: str | None = None
    subreddit: str
    created_utc: int
    num_comments: int | None = None
    source_api: str

    @computed_field
    @property
    def is_complete(self) -> bool:
        return all([self.title, self.selftext is not None,
                    self.url, self.author])
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/shared/contracts.py` | Modify | Add `RedditCandidate` model with `is_complete` computed field |
| `src/auto_reddit/reddit/client.py` | Modify | Implement `collect_candidates()`, per-provider adapters, cursor pagination loop, retry logic, fallback chain |
| `src/auto_reddit/config/settings.py` | Modify | Fix defaults: `max_daily_opportunities=8`, `daily_review_limit=8` |
| `src/auto_reddit/main.py` | Modify | Wire `collect_candidates()` call and pass result downstream |
| `tests/test_reddit/test_client.py` | Create | Unit tests: normalization per provider, pagination, fallback, incomplete marking, 7-day filter |
| `tests/test_reddit/conftest.py` | Create | Fixtures with sanitized raw snapshots from `docs/integrations/reddit/*/raw/` |

## Boundary with Change 2 and Change 3

| Concern | This change (1) | Change 2 (memory/uniqueness) | Change 3 (comments/context) |
|---------|-----------------|------------------------------|----------------------------|
| Post collection | YES — all `r/Odoo` posts in 7-day window | NO | NO |
| Cut to 8 | NO | YES | NO |
| `sent`/`rejected` exclusion | NO | YES | NO |
| Comments | NO | NO | YES |
| `old but alive` | NO | NO | NO (out of scope) |
| Persistence/SQLite | NO | YES | NO |

`collect_candidates()` returns `list[RedditCandidate]`. Change 2 consumes this list. Change 3 consumes posts selected by change 2. The contracts are the only coupling.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | Each `_normalize_*` adapter | Feed sanitized raw JSON fixtures, assert `RedditCandidate` fields |
| Unit | `is_complete` logic | Posts with/without optional fields |
| Unit | 7-day filter | Mock `datetime.now`, verify boundary posts in/out |
| Unit | Cursor pagination loop | Mock API returning 2 pages + stop condition |
| Unit | Fallback chain | Mock reddit3 fail → reddit34 success; all fail → empty list |
| Integration | Full `collect_candidates` | Mock HTTP layer (respx/responses), verify end-to-end flow |

## Migration / Rollout

No migration required. This is the first functional implementation of the `reddit/` module. Settings defaults change from 10→8, which is a correction to match operative docs, not a behavioral migration.

## Open Questions

- [ ] Exact `cursor` parameter name per API for page 2+ requests (reddit3 uses query param `cursor`, reddit34 and reddapi need verification — raws show cursor values but not the next-page request format). To be resolved during implementation via quick probe.
