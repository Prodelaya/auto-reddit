# Design: Telegram Daily Delivery

## Technical Approach

Add three collaborating components to the existing `delivery/`, `persistence/`, and orchestrator layers: (1) a **selector** that builds the deterministic daily delivery set from persisted `pending_delivery` records, applying TTL expiry and retry-first ordering within the cap; (2) a **renderer** that converts `AcceptedOpportunity` JSON into HTML strings without AI calls; (3) a **sender** that calls Telegram Bot API and reports per-message success/failure so the orchestrator can transition state.

`main.py` wires the three into a new delivery step after evaluation, using `CandidateStore` for reads and writes.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Selector lives in `delivery/` | `delivery/selector.py` — pure function `select_deliveries(records, now) → list[PostRecord]` | Put selection in `persistence/store.py` | Selection is delivery policy (retry-first, cap, TTL) not storage concern; keeps store as dumb CRUD |
| Renderer is a standalone module | `delivery/renderer.py` — pure function `render_opportunity(opp) → str`, `render_summary(opps) → str` | Inline in `telegram.py` | Testable without network; follows existing pattern of thin modules |
| Sender wraps httpx (sync) | `delivery/telegram.py` — `send_message(bot_token, chat_id, html) → bool` | aiohttp, python-telegram-bot lib | Project is sync everywhere; httpx is already stdlib-adjacent, minimal dep; returns bool matching `mark_sent` gate |
| TTL computed at selection time | Selector filters expired records before ordering | Purge expired rows in store | Non-destructive: expired records stay queryable for debugging; purge is a separate future concern |
| Summary is a single function call | `send_message(...)` for summary, failure logged, delivery loop continues | Separate summary pipeline | Matches spec: non-blocking, same transport |

## Data Flow

```
CandidateStore.get_pending_deliveries()
        │
        ▼
  select_deliveries(records, now)        ← TTL filter + retry-first + cap 8
        │
        ▼
  render_summary(selected) ──► send_message() ──► log success/failure (non-blocking)
        │
        ▼
  for each record in selected:
     AcceptedOpportunity.model_validate_json(record.opportunity_data)
        │
        ▼
     render_opportunity(opp) ──► send_message()
        │                              │
        ├── success ──► store.mark_sent(post_id)
        └── failure ──► log, skip (record stays pending_delivery)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/delivery/selector.py` | Create | Pure selection: TTL expiry filter, retry-first ordering by `decided_at` ASC, cap enforcement |
| `src/auto_reddit/delivery/renderer.py` | Create | Deterministic HTML rendering from `AcceptedOpportunity` fields; `render_opportunity()` + `render_summary()` |
| `src/auto_reddit/delivery/telegram.py` | Modify | Implement `send_message(bot_token, chat_id, html, parse_mode="HTML") → bool` via httpx POST to `sendMessage` |
| `src/auto_reddit/delivery/__init__.py` | Modify | Re-export `deliver_daily` façade function |
| `src/auto_reddit/persistence/store.py` | Modify | Add `purge_expired(now)` (optional cleanup, not required for correctness) |
| `src/auto_reddit/main.py` | Modify | Wire delivery step: get pending → select → render/send → mark_sent |
| `src/auto_reddit/config/settings.py` | Modify | Add `max_daily_deliveries: int = 8` (delivery cap, distinct from `daily_review_limit`) |
| `tests/test_delivery/test_selector.py` | Create | Unit tests: TTL filtering, retry-first ordering, cap enforcement |
| `tests/test_delivery/test_renderer.py` | Create | Unit tests: HTML output from known `AcceptedOpportunity` fixtures |
| `tests/test_delivery/test_telegram.py` | Create | Unit tests: send_message with mocked httpx |

## Interfaces / Contracts

```python
# delivery/selector.py
def select_deliveries(
    records: list[PostRecord],
    now: datetime,
    cap: int = 8,
) -> list[PostRecord]:
    """Return up to `cap` valid records: retries first (oldest decided_at), then new, TTL-expired excluded."""
    ...

def is_expired(record: PostRecord, now: datetime) -> bool:
    """Weekly TTL: Mon/Tue/Wed records expire Friday 23:59; Thu/Fri expire next Monday 23:59."""
    ...

# delivery/renderer.py
def render_opportunity(opp: AcceptedOpportunity) -> str:
    """Deterministic HTML from persisted fields. No AI. Includes warning/bullets if present."""
    ...

def render_summary(opportunities: list[AcceptedOpportunity], retry_count: int, new_count: int) -> str:
    """HTML summary: total count, retry vs new breakdown."""
    ...

# delivery/telegram.py
def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    """POST to api.telegram.org/bot{token}/sendMessage with parse_mode=HTML. Returns True on HTTP 200 + ok=true."""
    ...

# delivery/__init__.py
def deliver_daily(store: CandidateStore, settings: Settings) -> DeliveryReport:
    """Façade: select → render summary → send summary → render+send each → mark_sent on success."""
    ...
```

`DeliveryReport` — new Pydantic model in `shared/contracts.py`:

```python
class DeliveryReport(BaseModel):
    total_selected: int
    retries: int
    new: int
    sent_ok: int
    sent_failed: int
    summary_sent: bool
    expired_skipped: int
```

## TTL Algorithm

```
Given record.decided_at as Unix timestamp:
  weekday = date_from_ts(decided_at).weekday()  # 0=Mon ... 4=Fri
  if weekday in (0, 1, 2):   # Mon, Tue, Wed
      expiry = next_friday_2359(decided_at)
  elif weekday in (3, 4):    # Thu, Fri
      expiry = next_monday_2359(decided_at)
  else:                       # Sat, Sun (edge: evaluation shouldn't run, but defensive)
      expiry = next_monday_2359(decided_at)
  record is expired when now > expiry
```

## State Transitions

```
[AI accepts] ──► pending_delivery (persisted by evaluation step, NOT by delivery)
                       │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
   TTL expired    send success    send failure
   (excluded)     ──► sent        (stays pending_delivery,
                                   retried next run)
```

Invariants:
- `sent` is set ONLY by `store.mark_sent()` ONLY after `send_message()` returns `True`.
- A failed send NEVER changes state. No `rejected` from transport failure.
- Expired records are filtered out at selection time; their DB row is untouched.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `select_deliveries` — TTL, ordering, cap | Freeze `now`, build `PostRecord` fixtures with known `decided_at` weekdays |
| Unit | `render_opportunity`, `render_summary` — HTML output | Known `AcceptedOpportunity` → assert substrings, no network |
| Unit | `send_message` — HTTP interaction | Mock httpx; assert payload structure, parse_mode, return bool |
| Integration | `deliver_daily` façade | In-memory SQLite + mocked httpx; verify `mark_sent` called only on success |

## Migration / Rollout

No migration required. `post_decisions` table schema is unchanged. New Python files only. httpx added as runtime dependency via `uv add httpx`.

## Open Questions

- None. All decisions are closed per discovery and spec.
