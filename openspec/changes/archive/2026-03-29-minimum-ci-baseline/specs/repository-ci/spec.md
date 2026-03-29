# repository-ci Specification

## Purpose

Define the minimum repository CI contract so pushes and pull requests receive automatic verification through the existing `uv`-based test workflow without adding secrets, release behavior, or extra quality gates.

## Requirements

### Requirement: Validate changes on the main integration path

The repository CI baseline MUST run automatically on `push` to `main` and on `pull_request` events targeting `main`.

#### Scenario: Run baseline CI for a pull request

- GIVEN a pull request targets `main`
- WHEN GitHub evaluates repository workflows
- THEN the baseline CI workflow is triggered automatically
- AND the pull request receives a pass/fail signal from that run

#### Scenario: Ignore non-baseline branches and events

- GIVEN a workflow event is not `push` to `main` and not a pull request targeting `main`
- WHEN GitHub evaluates the baseline CI workflow
- THEN the baseline workflow is not required to run for that event

### Requirement: Execute repository verification only through uv

The baseline CI workflow MUST provision the repository Python version from `.python-version`, MUST install dependencies with `uv`, and MUST execute verification with `uv run pytest tests/ -x --tb=short`. The workflow MUST NOT introduce alternate package-install or test-entrypoint commands for this baseline.

#### Scenario: Run the standard verification command

- GIVEN the workflow job starts on a clean GitHub runner
- WHEN the baseline CI job prepares the project environment
- THEN it installs the configured Python runtime and project dependencies through `uv`
- AND it runs `uv run pytest tests/ -x --tb=short` as the verification step

### Requirement: Keep the baseline secrets-free and non-blocking for optional smoke coverage

The baseline CI workflow MUST succeed without repository secrets or live service credentials. Env-gated smoke coverage MAY exist in the test suite, but when its activation variables are absent, those tests MUST remain skipped by default and SHALL NOT fail the baseline run.

#### Scenario: Baseline CI runs without live credentials

- GIVEN no Reddit, Telegram, or other smoke-test credentials are available in CI
- WHEN the baseline workflow executes the standard pytest command
- THEN the run completes using only tests eligible for the default environment
- AND optional smoke tests are reported as skipped rather than blocking the workflow
