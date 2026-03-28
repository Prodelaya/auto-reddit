## Verification Report

**Change**: minimum-ci-baseline
**Version**: N/A

---

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 10 |
| Tasks complete | 10 |
| Tasks incomplete | 0 |

All tasks in `openspec/changes/minimum-ci-baseline/tasks.md` are marked complete.

---

### Build & Tests Execution

**Build**: ➖ Not configured
```text
No `rules.verify.build_command` is defined in `openspec/config.yaml`, so build/type-check execution was skipped.
```

**Tests**: ✅ 298 passed / ❌ 0 failed / ⚠️ 0 skipped
```text
$ uv run pytest tests/ -x --tb=short
298 passed in 31.06s
```

**Supplementary runtime evidence (credential-free smoke gate)**: ✅ 0 failed / ⚠️ 4 skipped
```text
$ REDDIT_SMOKE_API_KEY='' REDDIT_API_KEY='' TELEGRAM_SMOKE_BOT_TOKEN='' TELEGRAM_SMOKE_CHAT_ID='' uv run pytest tests/test_integration/test_operational.py -k "SmokeOptional" -rs
SKIPPED [1] tests/test_integration/test_operational.py:877: Neither REDDIT_SMOKE_API_KEY nor REDDIT_API_KEY is set — smoke tests skipped
SKIPPED [1] tests/test_integration/test_operational.py:916: TELEGRAM_SMOKE_BOT_TOKEN / TELEGRAM_SMOKE_CHAT_ID not set — Telegram smoke skipped
SKIPPED [1] tests/test_integration/test_operational.py:929: TELEGRAM_SMOKE_BOT_TOKEN / TELEGRAM_SMOKE_CHAT_ID not set — Telegram smoke skipped
SKIPPED [1] tests/test_integration/test_operational.py:942: TELEGRAM_SMOKE_BOT_TOKEN / TELEGRAM_SMOKE_CHAT_ID not set — Telegram smoke skipped
```

**Coverage**: ➖ Not configured

---

### Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Validate changes on the main integration path | Run baseline CI for a pull request | (none found) | ❌ UNTESTED |
| Validate changes on the main integration path | Ignore non-baseline branches and events | (none found) | ❌ UNTESTED |
| Execute repository verification only through uv | Run the standard verification command | (none found) | ❌ UNTESTED |
| Keep the baseline secrets-free and non-blocking for optional smoke coverage | Baseline CI runs without live credentials | `tests/test_integration/test_operational.py > TestRedditSmokeOptional / TestTelegramSmokeOptional` | ⚠️ PARTIAL |

**Compliance summary**: 0/4 scenarios compliant

Notes:
- The change has strong structural evidence in `.github/workflows/ci.yml`, but no automated test currently exercises GitHub Actions trigger semantics or the workflow file itself.
- The credential-free smoke behavior has runtime evidence, but only through a targeted supplementary pytest run with cleared env vars, not through a full workflow-level automated test.

---

### Correctness (Static — Structural Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Validate changes on the main integration path | ✅ Implemented | `.github/workflows/ci.yml` triggers on `push.branches: [main]` and `pull_request.branches: [main]`, with no extra event types or branches. |
| Execute repository verification only through uv | ⚠️ Partial | Workflow uses `astral-sh/setup-uv@v7`, `uv sync --dev`, and `uv run --frozen pytest tests/ -x --tb=short`. This stays uv-only, but it does **not** match the spec/proposal’s exact verification command (`uv run pytest tests/ -x --tb=short`) because of the added `--frozen` flag. External action docs also confirm `setup-uv` can respect `.python-version` when no `python-version:` input is supplied. |
| Keep the baseline secrets-free and non-blocking for optional smoke coverage | ✅ Implemented | `.github/workflows/ci.yml` references no secrets/env vars, and `tests/test_integration/test_operational.py` gates smoke coverage with `pytest.mark.skipif` on credential env vars. |

---

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Use `astral-sh/setup-uv@v7` without `actions/setup-python` | ✅ Yes | Workflow uses only `astral-sh/setup-uv@v7`. |
| Let uv read `.python-version` | ✅ Yes | Workflow omits `python-version:` and repo has `.python-version = 3.14`. |
| Enable uv cache | ✅ Yes | `enable-cache: true` is present. |
| Use a single `ubuntu-latest` job | ✅ Yes | One `test` job on `ubuntu-latest`. |
| Run `uv run --frozen pytest tests/ -x --tb=short` | ✅ Yes | Design and workflow match each other, but this choice deviates from the spec/proposal’s exact command. |
| File changes table | ✅ Yes | Only `.github/workflows/ci.yml` was needed and is present. |

---

### Issues Found

**CRITICAL** (must fix before archive):
- No automated runtime test proves the workflow triggers correctly for PRs to `main`.
- No automated runtime test proves the workflow ignores non-baseline branches/events.
- No automated runtime test proves the workflow executes the CI verification contract end-to-end.
- `.github/workflows/ci.yml` uses `uv run --frozen pytest tests/ -x --tb=short`, which deviates from the spec/proposal’s exact required command `uv run pytest tests/ -x --tb=short`.

**WARNING** (should fix):
- Build/type-check validation is not configured in `openspec/config.yaml`, so this verify phase could not provide build evidence.
- Credential-free smoke behavior was only partially validated through a targeted smoke subset run, not via a workflow-level test.

**SUGGESTION** (nice to have):
- Add a lightweight workflow-focused check (for example, a CI config test or actionlint-style validation) so trigger semantics and command shape are verified automatically.

---

### Verdict
FAIL

The implementation is structurally close and the repository test suite passes, but the change does not meet SDD verification quality gates because multiple spec scenarios are untested and the workflow command deviates from the spec’s exact baseline command.
