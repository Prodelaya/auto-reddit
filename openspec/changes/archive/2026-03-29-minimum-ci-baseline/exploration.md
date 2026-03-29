# Exploration: minimum-ci-baseline

## Current State

The repository has **zero CI automation** — no `.github/workflows/` directory exists.
The project is otherwise in solid shape for a first CI workflow:

- **Python version**: `3.14` (pinned via `.python-version`). Python `3.14.3` is
  **available in `actions/setup-python`** (confirmed from `actions/python-versions`
  releases; `3.14.3` published 2026-02-04 with 21 platform assets including
  `linux-22.04-x64` and `linux-24.04-x64`).
- **Package manager**: `uv` only (`AGENTS.md`, `openspec/config.yaml`). No pip,
  no setup.py. Official entry-point: `uv sync`, `uv run pytest`.
- **Test suite**: 273 tests collected. On clean `HEAD` (`c32e572`) all 273 pass in
  ~31 s. The current working tree has 15 failing tests, but those belong to the
  **in-flight** `runtime-documented-truth-alignment` change (uncommitted) — they
  are NOT a pre-existing regression; the last committed state is fully green.
- **Smoke tests** are **env-gated** (`@pytest.mark.skipif`) inside
  `test_integration/test_operational.py`. They skip silently when
  `REDDIT_SMOKE_API_KEY` / `TELEGRAM_SMOKE_BOT_TOKEN` / `TELEGRAM_SMOKE_CHAT_ID`
  are absent. The CI minimum does NOT need to set any of those.
- **No secrets required** for the safe suite — all non-smoke tests use
  `unittest.mock`, real SQLite via `tmp_path`, and local snapshot fixtures
  (`docs/integrations/reddit/*/raw/*.json`).
- **Build system**: `hatchling` src-layout (`src/auto_reddit/`). `pyproject.toml`
  declares `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and
  `pythonpath = ["src"]` — pytest finds everything without extra flags.
- **`python-dotenv`** is a dev dependency. `test_operational.py` calls
  `load_dotenv()` at module level, which is harmless when no `.env` file is
  present (it simply no-ops).

## Affected Areas

- `.github/workflows/` — does not exist; must be created (1 new file)
- `pyproject.toml` — no changes needed; pytest config already correct
- `tests/` — no changes needed; smoke tests already env-gated
- `openspec/discovery/minimum-ci-baseline.md` — artifact already exists,
  no changes needed

## Approaches

### 1. Single-job workflow (`push` + `pull_request` on `main`)

One workflow file, one job, sequential steps:
`setup-python` → `install uv` → `uv sync --dev` → `uv run pytest tests/ -x --tb=short`

- **Pros**: exactly matches the `AGENTS.md` test interface; minimal YAML; fast
  (~35–40 s including checkout + setup); zero secrets; directly portable from local
  dev; one signal — green/red
- **Cons**: no parallelism (not needed at this scale); no lint gate (out of scope)
- **Effort**: Low

### 2. Single-job workflow with explicit smoke-skip assertion

Same as #1 but adds `--no-header -q` to confirm skip count equals expected number
of smoke tests, so CI explicitly documents that skips are expected.

- **Pros**: self-documenting skip behavior
- **Cons**: skip count is fragile (breaks whenever a smoke test is added/removed);
  adds maintenance burden for zero added safety; smoke skip count is already
  readable from standard pytest output
- **Effort**: Low-Medium

### 3. Two-job workflow (lint + test, parallel)

Add a `ruff check` or `ruff format --check` job alongside the test job.

- **Pros**: catches style regressions
- **Cons**: `ruff` is NOT in `[project.optional-dependencies].dev` — adding it
  would be a separate concern; `AGENTS.md` says test interface is
  `uv run pytest tests/ -x --tb=short`; `minimum-ci-baseline` scope explicitly
  excludes "linting no estandarizado" (discovery brief §50)
- **Effort**: Medium

### 4. `uv` via `astral-sh/setup-uv` action

Use the official `astral-sh/setup-uv` GitHub Action instead of manually
installing `uv` via `pip install uv`.

- **Pros**: handles uv installation correctly; caches the uv binary; idiomatic
  for uv-based projects; let's `setup-uv` take care of Python via
  `python-version-file: .python-version` (it reads `.python-version` and installs
  the right Python via uv itself, potentially bypassing `actions/setup-python`)
- **Cons**: introduces a third-party action dependency; `setup-uv` with
  `python-version-file` makes `actions/setup-python` redundant
- **Effort**: Low

## Recommendation

**Approach 1 + Approach 4 combined** — a single workflow using
`astral-sh/setup-uv` with `python-version-file: .python-version`.

Rationale:
- `astral-sh/setup-uv` is the idiomatic way for uv projects on GitHub Actions;
  it reads `.python-version` and installs Python 3.14 via uv's managed Python
  (no separate `actions/setup-python` call needed; uv downloads the CPython
  toolchain itself).
- The command chain `uv sync --dev && uv run pytest tests/ -x --tb=short` maps
  **exactly** to the `AGENTS.md` interface — nothing to invent.
- Triggers: `push` to `main` and `pull_request` targeting `main`. These two
  cover the stated discovery brief trigger ("cada push o pull request").
- Smoke tests skip automatically; no special handling required — pytest output
  will show `N skipped` which is self-documenting.
- Single job, ~35 s total: checkout (2 s) + uv setup/Python install (~20 s, cached
  on warm runners) + `uv sync` (~5 s) + pytest (~31 s) = under 60 s on first run,
  under 40 s cached.

**Open decision from discovery brief** (now closed):
- *"Cerrar si el baseline corre solo en PR/push o tambien en otras señales"*:
  → `push` on `main` + `pull_request` targeting `main`. No `workflow_dispatch`,
  no schedule needed for a baseline.
- *"Cerrar si conviene separar job único o varios pasos dentro de un único workflow"*:
  → Single job with sequential steps. Two steps inside one job (install +
  test) is the correct split. No separate jobs.

## Risks

- **Python 3.14 availability**: Confirmed available as `3.14.3` in
  `actions/python-versions`. Risk = Low.
- **`astral-sh/setup-uv` stability**: Actively maintained official action by
  Astral (uv authors). Risk = Low; fallback is manual `pip install uv`.
- **Workflow triggers too broad**: Only `main` branch — this is intentional for
  minimum baseline; feature branches get coverage only when a PR is opened.
  Risk = acceptable (not a problem for a solo/small-team project).
- **Scope creep**: If the proposal tries to add coverage gates, linting, or
  release automation, the change stops being "minimum CI". Keep it strictly to
  one workflow file. Risk = Low if scoped correctly.
- **In-flight test failures on non-`main` branches**: Currently
  `runtime-documented-truth-alignment` has 15 failing tests in the working tree.
  The CI workflow will block that branch's PR until those tests are fixed — which
  is EXACTLY the correct behavior. Not a risk; it's the feature.

## Ready for Proposal

Yes — all open decisions are now closed, the technical approach is confirmed,
and the artifact is a single new file: `.github/workflows/ci.yml`.
