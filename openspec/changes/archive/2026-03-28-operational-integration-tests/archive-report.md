# Archive Report

**Change**: operational-integration-tests  
**Mode**: hybrid  
**Archived on**: 2026-03-28

## Archive Decision

Archive approved. The final verify outcome is **PASS** with **no critical issues, warnings, or suggestions**. The Reddit smoke test remains intentionally env-gated by `REDDIT_SMOKE_API_KEY` (with fallback to `REDDIT_API_KEY`), skipped by default, and non-blocking for standard verification, so its skipped status does not block archival.

## Final Verify Outcome Preserved

- **Verdict**: PASS
- **Full suite**: `uv run pytest tests/ -x --tb=short` → 269 passed, 1 skipped
- **Integration suite**: `uv run pytest tests/test_integration/test_operational.py -vv --tb=short` → 10 passed, 1 skipped
- **Non-blocking note preserved**: `TestRedditSmokeOptional::test_real_reddit_collect_candidates_returns_nonempty_list` is optional smoke coverage only; it is env-gated (`REDDIT_SMOKE_API_KEY` preferred, fallback `REDDIT_API_KEY`) and intentionally excluded from the pass/fail criteria for normal runs.

## Spec Sync

| Domain | Action | Details |
|--------|--------|---------|
| `operational-integration-tests` | Created | Promoted the full delta spec to `openspec/specs/operational-integration-tests/spec.md` |

## Artifact Lineage

- Project context (Engram): `#735` → `sdd-init/auto-reddit`
- Proposal (Engram): `#1357` → `sdd/operational-integration-tests/proposal`
- Spec (Engram): `#1359` → `sdd/operational-integration-tests/spec`
- Design (Engram): `#1361` → `sdd/operational-integration-tests/design`
- Tasks (Engram): `#1363` → `sdd/operational-integration-tests/tasks`
- Apply progress (Engram): `#1365` → `sdd/operational-integration-tests/apply-progress`
- Verify report (Engram): `#1369` → `sdd/operational-integration-tests/verify-report`

## Hybrid Traceability Note

The archive preserves both the consolidated main spec and the final filesystem artifacts for proposal, specs, design, tasks, verify, and archive reporting. The audit trail also preserves that the accepted P2 proof strategy is controlled empty-input traversal through `main.run()` with zero upstream side effects, not production refactoring.

## Post-Archive Correction (2026-03-28)

The smoke test env gate was updated to use a fallback strategy: `REDDIT_SMOKE_API_KEY` is preferred if present, otherwise `REDDIT_API_KEY` is used. This reflects the reality that most users configure a single `REDDIT_API_KEY` for all Reddit access and only set `REDDIT_SMOKE_API_KEY` when they want a separate key for smoke testing. No dedicated smoke key is required to exercise the smoke test.

## Post-Archive Correction (2026-03-28) — .env loading

The smoke test was skipping in manual runs because `os.getenv()` does not read `.env` files. Fixed by:
1. Adding `python-dotenv` to dev dependencies in `pyproject.toml`.
2. Adding `load_dotenv()` call before the env-gate in `test_operational.py`.

Result: smoke test now **passes** (270 passed, 0 skipped) when `.env` contains `REDDIT_API_KEY`. No production code changes.
