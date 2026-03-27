# Tasks: Candidate Memory and Uniqueness

## Phase 1: Foundation (contracts + config)

- [x] 1.1 Add `PostDecision` enum (`sent`, `rejected`, `pending_delivery`) to `src/auto_reddit/shared/contracts.py`
- [x] 1.2 Add `PostRecord` Pydantic model (`post_id`, `status: PostDecision`, `opportunity_data: str | None`, `decided_at: int`) to `src/auto_reddit/shared/contracts.py`
- [x] 1.3 Add `db_path: str = "auto_reddit.db"` field to `Settings` in `src/auto_reddit/config/settings.py`

## Phase 2: Core Implementation (CandidateStore)

- [x] 2.1 Implement `CandidateStore.__init__(db_path)` and `init_db()` in `src/auto_reddit/persistence/store.py` — creates SQLite table `post_decisions` with columns `post_id TEXT UNIQUE`, `status TEXT`, `opportunity_data TEXT`, `decided_at INTEGER`
- [x] 2.2 Implement `get_decided_post_ids() -> set[str]` — returns post_ids with status `sent` or `rejected`
- [x] 2.3 Implement `save_rejected(post_id)` — upserts record with status `rejected`, current timestamp
- [x] 2.4 Implement `save_pending_delivery(post_id, opportunity_data)` — upserts record with status `pending_delivery`
- [x] 2.5 Implement `mark_sent(post_id)` — updates existing record status to `sent`
- [x] 2.6 Implement `get_pending_deliveries() -> list[PostRecord]` — returns all `pending_delivery` records

## Phase 3: Integration (pipeline wiring)

- [x] 3.1 In `src/auto_reddit/main.py`, instantiate `CandidateStore(settings.db_path)` and call `init_db()` at pipeline start
- [x] 3.2 After `collect_candidates()`, call `store.get_decided_post_ids()`, filter out decided candidates, sort remaining by `created_utc` desc, slice `[:settings.daily_review_limit]`
- [x] 3.3 Log counts: total collected, excluded by memory, eligible after cut

## Phase 4: Testing

- [x] 4.1 Create `tests/test_persistence/test_store.py` — test `save_rejected` + `get_decided_post_ids` excludes rejected posts (spec scenario: filter eligible set)
- [x] 4.2 Test `save_pending_delivery` + `get_pending_deliveries` returns stored record with opportunity_data intact (spec scenario: retry without re-evaluation)
- [x] 4.3 Test `mark_sent` transitions `pending_delivery` → `sent` and `get_decided_post_ids` then includes it (spec scenario: close on delivery success)
- [x] 4.4 Test duplicate `post_id` insert is handled by upsert without error (UNIQUE constraint)
- [x] 4.5 Test pipeline exclusion+cut logic: given 12 candidates with 3 decided, result is 8 most recent undecided (spec scenario: filter and cut eligible set)
- [x] 4.6 Test a non-selected post has no persistence side-effect (spec scenario: keep non-selected posts out of persistence)
