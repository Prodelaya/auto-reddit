# Tasks: Minimum CI Baseline

## Phase 1: Infrastructure

- [x] 1.1 Create `.github/workflows/` directory structure
- [x] 1.2 Create `.github/workflows/ci.yml` with the workflow skeleton: `name: CI`, trigger block (`on: push` to `main`, `pull_request` targeting `main`), and the `test` job targeting `ubuntu-latest`

## Phase 2: Core Implementation

- [x] 2.1 Add checkout step using `actions/checkout@v4`
- [x] 2.2 Add uv install step using `astral-sh/setup-uv@v7` with `enable-cache: true`
- [x] 2.3 Add dependency install step: `uv sync --dev`
- [x] 2.4 Add test execution step: `uv run pytest tests/ -x --tb=short`

## Phase 3: Verification

- [x] 3.1 Validate `ci.yml` is syntactically valid YAML (local parse check)
- [x] 3.2 Verify workflow triggers match spec: `push` to `main` and `pull_request` targeting `main` only — no other branches or event types
- [x] 3.3 Verify no secrets, env vars, or credentials are referenced in the workflow file
- [x] 3.4 Confirm existing smoke tests use `pytest.mark.skipif` on env vars so they auto-skip without credentials (inspect test files)
- [x] 3.5 Run `uv run pytest tests/ -x --tb=short` locally to confirm the same command the CI will execute passes green

## Phase 4: Post-verify corrections (re-apply after FAIL verdict)

- [x] 4.1 Fix `ci.yml`: remove `--frozen` flag — change `uv run --frozen pytest` to `uv run pytest tests/ -x --tb=short` to match spec/proposal exactly
- [x] 4.2 Update `design.md` architecture decision table and data flow to reflect the corrected command (no `--frozen`)
- [x] 4.3 Create `tests/test_ci_workflow.py` with 22 automated tests covering all 4 spec scenarios (trigger semantics, command shape, secrets-free baseline, smoke skip behaviour) — stdlib only, no pyyaml required
- [x] 4.4 Confirm full suite passes: `uv run pytest tests/ -x --tb=short` → 316 passed, 4 skipped (smoke tests auto-skip without credentials)

## Phase 5: Bugfix — uv sync flag correction (re-apply)

- [x] 5.1 Fix `.github/workflows/ci.yml`: `uv sync --dev` → `uv sync --extra dev` (dev deps are in `[project.optional-dependencies].dev`, not `[dependency-groups]`; `--dev` flag is wrong)
- [x] 5.2 Update `tests/test_ci_workflow.py`: rename `test_workflow_uses_uv_sync_dev_for_deps` → `test_workflow_uses_uv_sync_extra_dev_for_deps` and fix assertion to match corrected command
- [x] 5.3 Validate: `uv sync --extra dev` + `uv run pytest tests/ -x --tb=short` → 340 passed, 3 skipped ✅

## Phase 6: Bugfix — CI collection failure (corrective re-apply 2026-03-29)

- [x] 6.1 Create `tests/conftest.py` with `os.environ.setdefault(...)` for all 4 required env vars (`DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `REDDIT_API_KEY`) to prevent `Settings()` ValidationError during pytest collection in CI (where no `.env` exists)
- [x] 6.2 Fix `tests/test_integration/test_operational.py`: change `_SMOKE_API_KEY` guard from `os.getenv("REDDIT_SMOKE_API_KEY") or os.getenv("REDDIT_API_KEY")` to `os.getenv("REDDIT_SMOKE_API_KEY")` only — prevents dummy `REDDIT_API_KEY` from conftest activating smoke tests with invalid credentials
- [x] 6.3 Validate: `uv run pytest tests/ -x --tb=short` → 339 passed, 4 skipped ✅
