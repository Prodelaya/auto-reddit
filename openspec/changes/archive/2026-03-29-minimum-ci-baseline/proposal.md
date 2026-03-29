# Proposal: Minimum CI Baseline

## Intent

Add the smallest versioned CI signal for this repo so pushes and PRs get automatic feedback on basic project health using the existing `uv` workflow, without introducing secrets, smoke dependencies, or broader platform concerns.

## Scope

### In Scope
- Add one GitHub Actions workflow at `.github/workflows/ci.yml`.
- Run on `push` to `main` and `pull_request` targeting `main`.
- Install Python 3.14 via `.python-version`, install deps with `uv`, and execute `uv run pytest tests/ -x --tb=short`.

### Out of Scope
- Linting, coverage gates, release automation, deploy, or multi-version matrices.
- Requiring live Reddit/Telegram smoke credentials or changing test behavior.

## Approach

Create a single-job GitHub Actions workflow using `astral-sh/setup-uv`, then run the repo’s official verification interface: `uv sync --dev` and `uv run pytest tests/ -x --tb=short`. Optional smoke tests remain skipped by default through their existing env-gated pytest markers.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `.github/workflows/ci.yml` | New | Minimum CI workflow for PR/push validation |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Scope creep beyond “minimum CI” | Med | Keep to one workflow and existing test command only |
| Confusion over skipped smoke tests | Low | Rely on existing env-gated skips and standard pytest output |

## Rollback Plan

Delete `.github/workflows/ci.yml` to fully remove the baseline; no product or runtime code changes are required.

## Dependencies

- GitHub Actions availability for repository workflows.
- Existing repo commands: `uv sync --dev` and `uv run pytest tests/ -x --tb=short`.

## Success Criteria

- [ ] The repo contains a versioned CI workflow for `push`/`pull_request` on `main`.
- [ ] CI installs and executes verification exclusively through `uv`.
- [ ] CI passes without requiring secrets or live smoke credentials.
- [ ] Optional smoke tests stay non-blocking and skipped by default in the baseline run.
