# Proposal: environment-persistence-execution-hardening

## Intent

The deployed model (ephemeral container + external cron + SQLite-on-volume) is documented but not enforced by configuration. When `DB_PATH` is unset, SQLite writes to `/app/auto_reddit.db` inside the container layer, silently bypassing the mounted volume at `/data`. Each run starts with an empty database. This change closes the gap by locking the operational contract into configuration and documentation — without touching pipeline logic.

## Scope

### In Scope
- Uncomment and set `DB_PATH=/data/auto_reddit.db` in `.env.example` with classification comment (deployed vs local)
- Add explicit `DB_PATH=/data/auto_reddit.db` to `docker-compose.yml` so `docker-compose up` is safe without a pre-configured `.env`
- Add **Section 10: Execution Contract** to `docs/architecture.md` with: mandatory/optional/smoke variable classification, volume contract (`/data` → named volume), and the exact cron invocation pattern
- Mark `docker-compose.yml` explicitly as the recommended deployment entrypoint in `docs/architecture.md`

### Out of Scope
- Changes to pipeline logic (`main.py`, any module)
- CI changes
- Broad documentation reorganization outside the execution contract section
- Fail-fast runtime validators in `settings.py`
- Changing `db_path` default in `settings.py` (kept as `"auto_reddit.db"` for local dev)

## Approach

Configuration-layer fix at three points:

1. **`.env.example`**: Uncomment `DB_PATH`, set to `/data/auto_reddit.db`, add a comment block distinguishing deployed mode (use `/data/auto_reddit.db`) from local dev (override with any local path or omit). Add a classification header to the smoke variables section to make the three-tier structure explicit.

2. **`docker-compose.yml`**: Add `environment:` block with `DB_PATH=/data/auto_reddit.db`. This makes `docker-compose up` correct even before `.env` is configured, acting as a safety net.

3. **`docs/architecture.md` §10 (new)**: Execution contract — env variable table (mandatory / optional / smoke-only), volume contract (`sqlite_data:/data` → `DB_PATH=/data/auto_reddit.db`), recommended cron syntax, and explicit statement that `docker-compose.yml` is the recommended entrypoint.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `.env.example` | Modified | Uncomment `DB_PATH`; add deployed/local annotation; reinforce smoke section header |
| `docker-compose.yml` | Modified | Add `environment: DB_PATH=/data/auto_reddit.db` |
| `docs/architecture.md` | Modified | Add §10 Execution Contract (env classification, volume contract, cron syntax) |
| `src/auto_reddit/config/settings.py` | None | Default stays `"auto_reddit.db"` — correct for local dev |
| Tests | None | All tests mock `db_path` via `tmp_path`; no breakage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `compose environment:` and `.env` both set `DB_PATH`, compose wins (correct) but may confuse | Low | Document precedence rule in §10; align both to same value |
| Developer runs locally with new `.env.example` default, writes to `/data/` which may not exist | Low | Add explicit local-dev override comment in `.env.example` |
| Perception that this is "just docs" and not a real fix | Low | Both `.env.example` and `compose` changes are executable configuration, not documentation |

## Rollback Plan

All changes are configuration and documentation only. To revert:
- `docker-compose.yml`: remove the `environment:` block
- `.env.example`: comment out `DB_PATH` again
- `docs/architecture.md`: remove §10

No database migrations, no code changes, no runtime state affected.

## Dependencies

None. This change is self-contained.

## Success Criteria

- [ ] `docker-compose up` with no pre-configured `.env` writes SQLite to `/data/auto_reddit.db` (inside the volume)
- [ ] `.env.example` has `DB_PATH` uncommented with a deployed/local annotation
- [ ] `docs/architecture.md` has a single section that classifies all env variables (mandatory, optional, smoke-only) and documents the cron invocation pattern
- [ ] A developer reading only `docs/architecture.md` can deploy the system correctly without consulting README or Dockerfile
- [ ] Existing tests pass without modification (`uv run pytest tests/ -x --tb=short`)
