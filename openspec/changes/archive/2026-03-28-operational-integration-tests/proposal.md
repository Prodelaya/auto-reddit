# Proposal: Operational Integration Tests

## Intent

Close the remaining operational-confidence gap around `main.run()` by proving the existing pipeline modules compose correctly at runtime. This change adds orchestration-focused integration tests only; it does not add product behavior.

## Scope

### In Scope
- Add `tests/test_integration/test_operational.py` and `tests/test_integration/__init__.py` for pipeline orchestration coverage.
- Prove retry-first delivery reuses persisted `opportunity_data` without AI re-evaluation, using real SQLite via `tmp_path`.
- Prove delivery and evaluation respect existing boundaries, plus optional Reddit smoke tests guarded by `REDDIT_SMOKE_API_KEY` and `pytest.mark.skipif`.

### Out of Scope
- Refactoring `main.run()` for dependency injection or other structural changes.
- New product functionality, Settings changes, coverage goals, or replacing existing unit tests.

## Approach

Exercise the real orchestration path while patching current external boundaries with `mock.patch` in caller namespaces. Use real `CandidateStore` SQLite files for multi-run scenarios, prioritize retry reuse before other boundary proofs, and keep Reddit smoke checks optional and non-blocking.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/test_integration/test_operational.py` | New | Operational integration tests for P1-P4 scenarios |
| `tests/test_integration/__init__.py` | New | Package marker for integration test location |
| `src/auto_reddit/main.py` | Verified | Runtime orchestration exercised without refactor |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Patch wrong namespace and miss real calls | Med | Patch symbols from `auto_reddit.main` caller boundary |
| Multi-run tests become flaky | Med | Use `tmp_path`, fixed data, and deterministic assertions |
| Optional smoke tests become CI blockers | Low | Guard with env-based `skipif`; exclude from success criteria |

## Rollback Plan

Remove the new integration test package if it proves noisy or unstable; production code remains unchanged.

## Dependencies

- Existing archived behaviors from candidate memory, thread extraction, AI evaluation, and Telegram delivery specs.
- `uv run pytest tests/ -x --tb=short`

## Success Criteria

- [ ] Retry reuse is proven without AI re-evaluation before other orchestration proofs.
- [ ] Delivery and evaluation boundary tests confirm no cross-boundary side effects.
- [ ] Multi-run SQLite tests prove `sent`/`rejected` exclusion while `pending_delivery` remains retryable.
- [ ] Optional Reddit smoke tests, if added, are env-gated and skipped by default.
