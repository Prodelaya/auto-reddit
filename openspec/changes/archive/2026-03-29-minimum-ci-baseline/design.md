# Design: Minimum CI Baseline

## Technical Approach

Single-file GitHub Actions workflow (`.github/workflows/ci.yml`) that mirrors the local developer verification command exactly: `uv sync --extra dev && uv run pytest tests/ -x --tb=short`. Uses `astral-sh/setup-uv@v7` for uv installation and caching. Python 3.14 is read from `.python-version` by uv automatically — no explicit version pin in the workflow.

> **Note (post-apply correction)**: The initial design documented `uv sync --dev`, but this repo declares dev dependencies under `[project.optional-dependencies].dev` in `pyproject.toml`, not under `[dependency-groups]`. The `--dev` flag targets `[dependency-groups]` only; the correct command is `uv sync --extra dev`. The workflow and this design now reflect the implemented truth.

## Architecture Decisions

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| `astral-sh/setup-uv@v7` (no `actions/setup-python`) | `actions/setup-python` + pip install uv | `setup-uv` handles uv install, Python provisioning, and cache in one step. Matches project's uv-only tooling constraint. |
| Let uv read `.python-version` (no `python-version:` input) | Hardcode `python-version: "3.14"` in workflow | Single source of truth — `.python-version` already pins 3.14. No drift between local and CI. |
| `enable-cache: true` | No caching | Default on GitHub-hosted runners; near-zero config cost, significant speedup on repeat runs. |
| Single `ubuntu-latest` job | OS matrix / Python version matrix | Proposal explicitly excludes multi-version matrices. One job = minimum viable signal. |
| `uv sync --extra dev` (not `--dev`) | `uv sync --dev` | This repo uses `[project.optional-dependencies].dev` in `pyproject.toml`. `uv sync --dev` targets `[dependency-groups]` only — pytest is not installed. `--extra dev` installs optional deps including pytest. |
| No `--frozen` flag on pytest run | `uv run --frozen pytest` | Spec/proposal mandate `uv run pytest tests/ -x --tb=short` exactly. `uv sync --extra dev` already resolves deps; `--frozen` is redundant and deviates from the documented developer command. |

## Data Flow

```
push/PR to main
      │
      ▼
GitHub Actions trigger
      │
      ▼
checkout ──→ setup-uv (install uv + Python 3.14 from .python-version + cache)
                │
                ▼
         uv sync --extra dev (install all deps incl. pytest, pytest-cov, python-dotenv)
                │
                ▼
         uv run pytest tests/ -x --tb=short
                │
                ▼
         ✅ pass / ❌ fail → PR status check
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `.github/workflows/ci.yml` | Create | Single-job CI workflow: checkout → setup-uv → sync → pytest |

## Interfaces / Contracts

Workflow YAML — the only artifact:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest tests/ -x --tb=short
```

Key contract points:
- **Triggers**: `push` to `main`, `pull_request` targeting `main`.
- **No secrets required**: Smoke tests use `pytest.mark.skipif` on env vars (`REDDIT_SMOKE_API_KEY`, `TELEGRAM_SMOKE_BOT_TOKEN`, `TELEGRAM_SMOKE_CHAT_ID`). Without those vars, they auto-skip — zero CI config needed.
- **Exit code**: pytest returns 0 on pass, non-zero on failure — GitHub Actions maps this directly to check status.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Verification | Workflow syntax is valid YAML | Push to branch and observe Actions tab |
| Functional | All non-smoke tests pass in CI | First PR run confirms green status |
| Smoke gate | Smoke tests skip without env vars | Verify pytest output shows `SKIPPED` for smoke classes |

No new test code needed — the CI workflow runs existing tests.

## Migration / Rollout

No migration required. Adding the workflow file is additive — no existing behavior changes. Rollback: delete `.github/workflows/ci.yml`.

## Open Questions

None — the scope is deliberately minimal and fully defined by the proposal.
