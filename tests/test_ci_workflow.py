"""Tests for the GitHub Actions CI workflow configuration.

Covers the spec scenarios for `minimum-ci-baseline`:
- Validate changes on the main integration path
  - Scenario: Run baseline CI for a pull request
  - Scenario: Ignore non-baseline branches and events
- Execute repository verification only through uv
  - Scenario: Run the standard verification command
- Keep the baseline secrets-free and non-blocking for optional smoke coverage
  - Scenario: Baseline CI runs without live credentials

Uses only stdlib — no pyyaml dependency required.
The workflow YAML is well-structured and predictable; text-based assertions
are sufficient and avoid introducing extra test dependencies.
"""

from __future__ import annotations

import pathlib
import re

import pytest

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

WORKFLOW_PATH = (
    pathlib.Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"
)


@pytest.fixture(scope="module")
def workflow_text() -> str:
    """Load the raw CI workflow YAML text once for all tests in this module."""
    assert WORKFLOW_PATH.exists(), (
        f"CI workflow file not found at {WORKFLOW_PATH}. "
        "Expected `.github/workflows/ci.yml` to exist."
    )
    return WORKFLOW_PATH.read_text()


# ---------------------------------------------------------------------------
# Scenario: Run baseline CI for a pull request
# Requirement: Validate changes on the main integration path
# ---------------------------------------------------------------------------


class TestMainIntegrationPathTriggers:
    """Spec: Validate changes on the main integration path."""

    def test_workflow_file_exists(self):
        """Workflow file MUST exist at `.github/workflows/ci.yml`."""
        assert WORKFLOW_PATH.exists(), f"CI workflow file not found at {WORKFLOW_PATH}."

    def test_workflow_triggers_on_push_to_main(self, workflow_text: str):
        """Workflow MUST trigger on push to main branch.

        The spec requires:
            GIVEN a push targets main
            THEN the baseline CI workflow is triggered automatically
        """
        # Match push block containing branches: [main]
        assert re.search(
            r"push:\s*\n\s+branches:\s*\[main\]", workflow_text
        ) or re.search(r"push:.*?\n.*?branches:.*?main", workflow_text, re.DOTALL), (
            "Workflow must declare 'push' trigger with 'branches: [main]'. "
            f"Current trigger block:\n{workflow_text}"
        )
        assert "push:" in workflow_text, "Workflow must have a 'push:' trigger."
        # Verify main is in the on block near push
        push_idx = workflow_text.index("push:")
        nearby = workflow_text[push_idx : push_idx + 100]
        assert "main" in nearby, (
            f"'main' branch not found in push trigger config. Context: {nearby!r}"
        )

    def test_workflow_triggers_on_pull_request_targeting_main(self, workflow_text: str):
        """Workflow MUST trigger on pull_request events targeting main.

        The spec requires:
            GIVEN a pull request targets main
            WHEN GitHub evaluates repository workflows
            THEN the baseline CI workflow is triggered automatically
        """
        assert "pull_request:" in workflow_text, (
            "Workflow must have a 'pull_request:' trigger."
        )
        pr_idx = workflow_text.index("pull_request:")
        nearby = workflow_text[pr_idx : pr_idx + 100]
        assert "main" in nearby, (
            f"'main' branch not found in pull_request trigger config. Context: {nearby!r}"
        )

    def test_workflow_has_on_block(self, workflow_text: str):
        """Workflow MUST have an 'on:' trigger block."""
        assert "\non:" in workflow_text or workflow_text.startswith("on:"), (
            "Workflow must have an 'on:' trigger block."
        )

    def test_workflow_has_jobs_block(self, workflow_text: str):
        """Workflow MUST have a 'jobs:' block."""
        assert "jobs:" in workflow_text, "Workflow must have a 'jobs:' block."


# ---------------------------------------------------------------------------
# Scenario: Ignore non-baseline branches and events
# Requirement: Validate changes on the main integration path
# ---------------------------------------------------------------------------


class TestNonBaselineEventsIgnored:
    """Spec: Workflow is not required to run for non-baseline events."""

    def test_push_trigger_restricted_to_main_only(self, workflow_text: str):
        """Push trigger MUST contain only 'main' — no extra branches.

        The spec requires:
            GIVEN a workflow event is not push to main
            THEN the baseline workflow is not required to run
        """
        push_match = re.search(r"push:\s*\n\s+branches:\s*\[([^\]]+)\]", workflow_text)
        if push_match:
            branches_str = push_match.group(1)
            branches = [b.strip() for b in branches_str.split(",")]
            assert branches == ["main"], (
                f"Push trigger must be restricted to ['main'] only. Found: {branches}"
            )

    def test_pull_request_trigger_restricted_to_main_only(self, workflow_text: str):
        """Pull request trigger MUST contain only 'main' — no extra branches."""
        pr_match = re.search(
            r"pull_request:\s*\n\s+branches:\s*\[([^\]]+)\]", workflow_text
        )
        if pr_match:
            branches_str = pr_match.group(1)
            branches = [b.strip() for b in branches_str.split(",")]
            assert branches == ["main"], (
                f"Pull request trigger must be restricted to ['main'] only. Found: {branches}"
            )

    def test_no_schedule_or_workflow_dispatch_event(self, workflow_text: str):
        """Workflow MUST NOT declare schedule or workflow_dispatch for the minimum baseline."""
        assert "schedule:" not in workflow_text, (
            "Workflow must not declare 'schedule:' event — minimum baseline only."
        )
        assert "workflow_dispatch:" not in workflow_text, (
            "Workflow must not declare 'workflow_dispatch:' event — minimum baseline only."
        )


# ---------------------------------------------------------------------------
# Scenario: Run the standard verification command
# Requirement: Execute repository verification only through uv
# ---------------------------------------------------------------------------


class TestStandardVerificationCommand:
    """Spec: Workflow MUST execute `uv run pytest tests/ -x --tb=short` exactly."""

    def test_workflow_uses_exact_pytest_command(self, workflow_text: str):
        """Workflow run step MUST contain `uv run pytest tests/ -x --tb=short`.

        The spec requires:
            GIVEN the workflow job starts on a clean GitHub runner
            THEN it runs `uv run pytest tests/ -x --tb=short` as the verification step

        Note: `uv run --frozen pytest` is explicitly NOT allowed — it deviates
        from the spec/proposal's exact required command.
        """
        expected = "uv run pytest tests/ -x --tb=short"
        assert expected in workflow_text, (
            f"Workflow must contain the exact command '{expected}'. "
            "The spec mandates this exact string — no --frozen or other flags."
        )

    def test_workflow_does_not_use_frozen_flag(self, workflow_text: str):
        """Workflow MUST NOT use `uv run --frozen pytest` — spec prohibits extra flags."""
        assert "uv run --frozen pytest" not in workflow_text, (
            "Workflow must not use '--frozen' flag. "
            "The spec/proposal require exactly `uv run pytest tests/ -x --tb=short`."
        )

    def test_workflow_uses_uv_sync_dev_for_deps(self, workflow_text: str):
        """Workflow MUST use `uv sync --dev` for dependency installation."""
        assert "uv sync --dev" in workflow_text, (
            "Workflow must install dependencies with 'uv sync --dev'."
        )

    def test_workflow_uses_no_pip_or_alternate_installers(self, workflow_text: str):
        """Workflow MUST NOT use pip, poetry, or other non-uv installers."""
        for forbidden in ["pip install", "poetry install", "pipenv install"]:
            assert forbidden not in workflow_text, (
                f"Forbidden installer '{forbidden}' found in workflow. "
                "CI must use only uv."
            )

    def test_workflow_uses_setup_uv_action(self, workflow_text: str):
        """Workflow MUST use `astral-sh/setup-uv` action."""
        assert "astral-sh/setup-uv" in workflow_text, (
            "Workflow must use 'astral-sh/setup-uv' action for uv installation."
        )

    def test_workflow_does_not_use_setup_python_action(self, workflow_text: str):
        """Workflow MUST NOT use `actions/setup-python` — setup-uv handles Python."""
        assert "actions/setup-python" not in workflow_text, (
            "Workflow must not use 'actions/setup-python'. "
            "setup-uv handles Python provisioning via .python-version."
        )

    def test_workflow_does_not_pin_python_version(self, workflow_text: str):
        """Workflow MUST NOT hardcode python-version — let uv read .python-version."""
        assert "python-version:" not in workflow_text, (
            "Workflow must not hardcode 'python-version:'. "
            "Let uv read '.python-version' for a single source of truth."
        )

    def test_workflow_enables_uv_cache(self, workflow_text: str):
        """Workflow MUST enable uv cache for performance."""
        assert "enable-cache: true" in workflow_text, (
            "Workflow must set 'enable-cache: true' on the setup-uv step."
        )

    def test_workflow_uses_ubuntu_latest_runner(self, workflow_text: str):
        """Workflow MUST use ubuntu-latest as the runner."""
        assert "ubuntu-latest" in workflow_text, (
            "Workflow must declare 'ubuntu-latest' as the runner."
        )

    def test_workflow_uses_checkout_action(self, workflow_text: str):
        """Workflow MUST use `actions/checkout@v4` as the first step."""
        assert "actions/checkout@v4" in workflow_text, (
            "Workflow must use 'actions/checkout@v4' to check out the repo."
        )

    def test_workflow_has_single_job(self, workflow_text: str):
        """Workflow MUST define exactly one job for the minimum baseline."""
        # Count top-level job entries by matching `  <job-name>:` under `jobs:`
        jobs_idx = workflow_text.index("jobs:")
        jobs_section = workflow_text[jobs_idx:]
        # Each job at indent level 2 starts with exactly 2 spaces followed by non-space
        job_entries = re.findall(r"^  \w[\w-]*:\s*$", jobs_section, re.MULTILINE)
        assert len(job_entries) == 1, (
            f"Workflow must have exactly 1 job. Found {len(job_entries)}: {job_entries}"
        )


# ---------------------------------------------------------------------------
# Scenario: Baseline CI runs without live credentials
# Requirement: Keep the baseline secrets-free and non-blocking
# ---------------------------------------------------------------------------


class TestSecretsFreeCIBaseline:
    """Spec: CI MUST succeed without repository secrets or live credentials."""

    def test_workflow_references_no_secrets(self, workflow_text: str):
        """Workflow MUST NOT reference ${{ secrets.* }} variables."""
        assert "secrets." not in workflow_text, (
            "Workflow must not reference any repository secrets. "
            "Found 'secrets.' reference — baseline must be credential-free."
        )

    def test_workflow_defines_no_credential_env_vars(self, workflow_text: str):
        """Workflow MUST NOT define credential-like env vars."""
        credential_patterns = ["API_KEY", "BOT_TOKEN", "REDDIT_", "TELEGRAM_"]
        for pattern in credential_patterns:
            assert pattern not in workflow_text, (
                f"Workflow references credential-like pattern '{pattern}'. "
                "CI baseline must be entirely secrets-free."
            )

    def test_smoke_tests_use_skipif_on_env_vars(self):
        """Smoke tests MUST use pytest.mark.skipif gated on env vars so they auto-skip in CI.

        The spec requires:
            GIVEN no credentials are available in CI
            THEN optional smoke tests are reported as skipped rather than blocking
        """
        smoke_file = (
            pathlib.Path(__file__).parent / "test_integration" / "test_operational.py"
        )
        assert smoke_file.exists(), f"Expected smoke test file at {smoke_file}."
        content = smoke_file.read_text()
        assert "pytest.mark.skipif" in content, (
            "Smoke tests must use `pytest.mark.skipif` so they auto-skip in CI "
            "when no credentials are available."
        )
        credential_env_vars = [
            "REDDIT_SMOKE_API_KEY",
            "REDDIT_API_KEY",
            "TELEGRAM_SMOKE_BOT_TOKEN",
        ]
        assert any(var in content for var in credential_env_vars), (
            "Smoke tests must gate on at least one credential env var "
            f"({credential_env_vars}) via skipif."
        )
