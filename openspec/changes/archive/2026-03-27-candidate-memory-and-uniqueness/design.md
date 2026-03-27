# Design: Candidate Memory and Uniqueness

## Technical Approach

Add a SQLite-backed operational store in `persistence/store.py` that tracks final business decisions (`sent`, `rejected`) and a transient pre-send record (`pending_delivery`). The orchestrator in `main.py` queries the store to exclude decided posts, applies the top-8 recency cut on the remaining eligible set, and closes the `sent` state only after confirmed Telegram delivery.

## Architecture Decisions

| Decision | Alternatives | Rationale |
|----------|-------------|-----------|
| **SQLite single-table with `status` column** (`sent`, `rejected`, `pending_delivery`) | Separate tables per status; JSON file store | Single table is simplest for query/purge with TTL. SQLite already implied by the `persistence/` module docstring. Aligns with ephemeral Docker deployment (single volume-mounted file). |
| **`pending_delivery` as the transient pre-send label** | `accepted`, `queued`, no label (implicit) | Makes the operational vs. final distinction explicit without overloading `approved`. It communicates "AI said yes, Telegram hasn't confirmed yet". Not a business state — purely operational. |
| **Filtering logic lives in `persistence/` as a pure query; cut logic in `main.py`** | All in `main.py`; all in `persistence/` | `persistence/` owns data access (what post_ids have decisions). `main.py` owns pipeline sequencing (top-8 cut, ordering). Respects module boundaries from `python-conventions`. |
| **Store keyed on `post_id` with UNIQUE constraint** | Composite key with subreddit | All posts come from r/Odoo; `post_id` is globally unique within Reddit. Simpler schema. |
| **No TTL/purge in this change** | Add purge now | Purge is operational maintenance, not part of memory-and-uniqueness semantics. Can be a follow-up task or added during `telegram-daily-delivery`. |

## Data Flow

```
collect_candidates()          persistence/store.py              main.py
      │                              │                              │
      ├── list[RedditCandidate] ────→│                              │
      │                              │← get_decided_post_ids() ────│
      │                              │                              │
      │                              │  exclude sent+rejected ─────→│
      │                              │                              ├── sort by created_utc desc
      │                              │                              ├── slice [:8]
      │                              │                              │
      │                              │                     (future: AI evaluation)
      │                              │                              │
      │                              │← save_pending_delivery() ───│  (after AI accept)
      │                              │← save_rejected() ───────────│  (after AI reject)
      │                              │                              │
      │                              │                     (future: Telegram delivery)
      │                              │                              │
      │                              │← mark_sent() ──────────────│  (only after TG success)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/shared/contracts.py` | Modify | Add `PostDecision` enum (`sent`, `rejected`, `pending_delivery`) and `PostRecord` Pydantic model for store rows. |
| `src/auto_reddit/persistence/store.py` | Modify | Implement `CandidateStore` class: `init_db()`, `get_decided_post_ids() → set[str]`, `save_rejected(post_id)`, `save_pending_delivery(post_id, opportunity_data)`, `mark_sent(post_id)`, `get_pending_deliveries() → list[PostRecord]`. |
| `src/auto_reddit/main.py` | Modify | After `collect_candidates`, call store to exclude decided posts, apply top-8 cut. Wire placeholders for AI → `save_rejected`/`save_pending_delivery` and delivery → `mark_sent`. |
| `src/auto_reddit/config/settings.py` | Modify | Add `db_path: str = "auto_reddit.db"` setting. |
| `tests/test_persistence/test_store.py` | Create | Unit tests for all store operations against in-memory SQLite. |

## Interfaces / Contracts

```python
# shared/contracts.py additions

class PostDecision(str, Enum):
    sent = "sent"
    rejected = "rejected"
    pending_delivery = "pending_delivery"

class PostRecord(BaseModel):
    post_id: str
    status: PostDecision
    opportunity_data: str | None = None  # JSON blob from AI, only for pending_delivery
    decided_at: int  # UTC timestamp

# persistence/store.py public interface

class CandidateStore:
    def __init__(self, db_path: str) -> None: ...
    def init_db(self) -> None: ...
    def get_decided_post_ids(self) -> set[str]: ...
    def save_rejected(self, post_id: str) -> None: ...
    def save_pending_delivery(self, post_id: str, opportunity_data: str) -> None: ...
    def mark_sent(self, post_id: str) -> None: ...
    def get_pending_deliveries(self) -> list[PostRecord]: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `CandidateStore` CRUD: insert rejected, insert pending_delivery, mark_sent, get_decided_post_ids, get_pending_deliveries, duplicate post_id handling | In-memory SQLite (`:memory:`), pytest fixtures |
| Unit | Top-8 cut and exclusion logic in orchestrator helper | Pure function with mock store returning known post_id sets |
| Unit | `PostDecision` enum and `PostRecord` serialization | Direct Pydantic model assertions |
| Integration | Full pipeline: collect → exclude → cut → (stub AI) → persist → (stub TG) → mark_sent | Mock HTTP + in-memory SQLite, end-to-end in `main.run()` |

## Migration / Rollout

No migration required. The SQLite database is created on first run via `init_db()`. The Docker volume mount ensures the `.db` file persists across ephemeral container restarts.

## Open Questions

- None. The naming of `pending_delivery` for the transient pre-send state resolves the only open decision from the discovery brief.
