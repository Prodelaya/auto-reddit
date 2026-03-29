# Exploration: environment-persistence-execution-hardening

## Current State

The system documents an ephemeral container + external cron + persistent SQLite-on-volume model.
However, the configuration chain has a concrete misalignment that breaks that contract silently:

| File | Key fact |
|---|---|
| `docker-compose.yml` | Mounts named volume `sqlite_data` at `/data` inside container |
| `Dockerfile` | Sets `WORKDIR /app` |
| `config/settings.py` | `db_path: str = "auto_reddit.db"` (default, relative path) |
| `.env.example` | `# DB_PATH=auto_reddit.db` (commented out — optional) |
| `docs/architecture.md §4` | Declares "SQLite (fichero en volumen Docker)" as persistence model |
| `README.md` | Confirms ephemeral container + cron + SQLite-in-volume model |

**The gap**: When the container runs without `DB_PATH` explicitly set to `/data/auto_reddit.db`,
SQLite writes to `/app/auto_reddit.db` (inside the container layer), NOT inside the volume at `/data`.
The volume is mounted but never used. Each ephemeral run starts with an empty database.
This silently destroys persistence while `docker-compose up` succeeds without any error.

### Variable contract gaps

`.env.example` has no classification of variables by role. Current implicit state:

| Variable | Mandatory | Classified? | Notes |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | Yes | ✓ (comment) | Required — pydantic-settings raises if absent |
| `TELEGRAM_BOT_TOKEN` | Yes | ✓ (comment) | Required |
| `TELEGRAM_CHAT_ID` | Yes | ✓ (comment) | Required |
| `REDDIT_API_KEY` | Yes | ✓ (comment) | Required |
| `DB_PATH` | **No, but critical** | Partial | Commented out; default silently breaks persistence |
| `MAX_DAILY_OPPORTUNITIES` | No | ✓ | Behavioral cap |
| `REVIEW_WINDOW_DAYS` | No | ✓ | Behavioral |
| `DAILY_REVIEW_LIMIT` | No | ✓ | Behavioral |
| `DEEPSEEK_MODEL` | No | ✓ | Model override |
| `REDDIT_SMOKE_API_KEY` | No | ✓ (smoke) | Only for integration tests |
| `TELEGRAM_SMOKE_BOT_TOKEN` | No | ✓ (smoke) | Only for integration tests |
| `TELEGRAM_SMOKE_CHAT_ID` | No | ✓ (smoke) | Only for integration tests |

`DB_PATH` is not required by pydantic-settings (has default), but its default value is
**operationally wrong** for the deployed Docker model. This is the central hardening gap.

### Execution contract gaps

`docs/architecture.md` states the operational model (§3) but does NOT specify:
- The exact `docker run` or `docker-compose` invocation with cron
- That `DB_PATH=/data/auto_reddit.db` is the required value when deployed
- How cron should invoke the container

`README.md` mentions ephemeral container + cron but provides no concrete command.

No single artifact currently closes the "how to run this correctly" contract.

## Affected Areas

- `docker-compose.yml` — needs `DB_PATH=/data/auto_reddit.db` either via env_file or inline env
- `.env.example` — needs `DB_PATH=/data/auto_reddit.db` uncommented and marked as required-for-deployed-mode
- `docs/architecture.md` — the resolved primary operational artifact; needs an execution contract section (cron command, DB_PATH requirement, volume contract)
- `src/auto_reddit/config/settings.py` — `db_path` default `"auto_reddit.db"` is fine for local dev/tests; no code change needed if `.env.example` and compose fix it declaratively
- `README.md` — minor: reference to `docs/architecture.md` for operational deployment; no rewrite

## Approaches

### 1. Fix at source: `.env.example` + `docker-compose.yml` + architecture doc section
- Set `DB_PATH=/data/auto_reddit.db` explicitly in `.env.example` (uncommented, with classification comment)
- Add inline `environment:` or env override in `docker-compose.yml` as safety net
- Add an "Execution contract" section to `docs/architecture.md` with: cron syntax, DB_PATH requirement, volume contract, and env classification table
- **Pros**: Closes gap at every layer; `docker-compose up` just works; docs = single truth
- **Cons**: Minimal; none significant
- **Effort**: Low

### 2. Fail-fast in settings: validate DB_PATH ends up inside `/data` when in container
- Add a startup validator that checks path prefix when inside a Docker context
- **Pros**: Runtime protection
- **Cons**: Over-engineering for a configuration problem; adds complexity and Docker-detection heuristics; not aligned with "hardening without changing pipeline logic"
- **Effort**: Medium

### 3. Hardcode `/data/auto_reddit.db` as default in `settings.py`
- Change `db_path: str = "/data/auto_reddit.db"` directly
- **Pros**: Container always correct without env
- **Cons**: Breaks local dev (writes to `/data/` which may not exist); breaks all tests that don't mock db_path; changes behavior without config
- **Effort**: Low — but wrong

## Recommendation

**Approach 1**: Fix at the configuration layer (`.env.example`, `docker-compose.yml`, `docs/architecture.md`).

This is the correct level of intervention:
- The pipeline logic is correct; the contract is what's missing
- `settings.py` default stays as `"auto_reddit.db"` for local dev compatibility
- `docker-compose.yml` becomes the de-facto deployment entrypoint (per resolved decision)
- `docs/architecture.md` becomes the single operational truth (per resolved decision)
- `.env.example` gets `DB_PATH=/data/auto_reddit.db` uncommented + a classification header

The execution contract section in `docs/architecture.md` should include:
1. Mandatory vs optional vs smoke-only variable classification
2. The exact cron line or `docker-compose run` invocation
3. The volume contract (`/data` = named volume = SQLite persists across runs)
4. The `DB_PATH` requirement for deployed mode

## Risks

- If `docker-compose.yml` sets `DB_PATH` via `environment:` AND `.env` also sets it, compose env takes precedence — need to document clearly or use env_file only to avoid confusion
- Tests in `test_operational.py` already mock `settings.db_path` via `_make_settings(tmp_path)` — no test breakage
- `test_store.py` uses `tmp_path` fixtures — no test breakage
- The `.env.example` change makes `DB_PATH` a visible, uncommented default — this is intentional; it may surprise developers who run locally without Docker (they'll get `/data/auto_reddit.db` which may not exist). Mitigation: add a comment distinguishing deployed vs local value

## Ready for Proposal

Yes. Problem is precise, scope is narrow, approach is clear, no open decisions remain.
