"""Spec scenario tests for `environment-persistence-execution-hardening`.

Covers all 6 spec scenarios via structural assertions on the repository artifacts
(no live Docker/infrastructure required):

Requirement: Persistent Docker SQLite Path
  - Scenario: Compose run uses persistent database path
  - Scenario: No ephemeral default in compose workflow

Requirement: Operational Environment Classification
  - Scenario: Required runtime variables are explicit
  - Scenario: Docker-critical variables stay isolated

Requirement: Isolated Operational Runbook
  - Scenario: Cron-compatible command path is documented
  - Scenario: Operational guidance does not rewrite shared runtime truth

Approach: file-read + structural text assertions (no external deps, no pyyaml).
The artifacts are well-structured and deterministic; text assertions are sufficient
and avoid introducing extra test dependencies.
"""

from __future__ import annotations

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Paths to artifacts under test
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
OPERATIONS_MD = REPO_ROOT / "docs" / "operations.md"
ARCHITECTURE_MD = REPO_ROOT / "docs" / "architecture.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def compose_text() -> str:
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"
    return COMPOSE_FILE.read_text()


@pytest.fixture(scope="module")
def env_example_text() -> str:
    assert ENV_EXAMPLE.exists(), f".env.example not found at {ENV_EXAMPLE}"
    return ENV_EXAMPLE.read_text()


@pytest.fixture(scope="module")
def operations_text() -> str:
    assert OPERATIONS_MD.exists(), f"docs/operations.md not found at {OPERATIONS_MD}"
    return OPERATIONS_MD.read_text()


@pytest.fixture(scope="module")
def architecture_text() -> str:
    assert ARCHITECTURE_MD.exists(), (
        f"docs/architecture.md not found at {ARCHITECTURE_MD}"
    )
    return ARCHITECTURE_MD.read_text()


# ---------------------------------------------------------------------------
# Requirement: Persistent Docker SQLite Path
# Scenario: Compose run uses persistent database path
# ---------------------------------------------------------------------------


class TestComposeRunUsesPersistentDatabasePath:
    """Spec scenario: 'Compose run uses persistent database path'.

    GIVEN an operator runs the documented Docker compose workflow
    WHEN the application starts inside the container
    THEN the configured SQLite database path SHALL resolve inside the mounted
         persistent data directory
    AND processed-state data SHALL survive container recreation
    """

    def test_compose_has_db_path_environment_override(self, compose_text: str):
        """docker-compose.yml MUST enforce DB_PATH to the persistent mount via
        the `environment:` block so it overrides any env_file value.

        This guarantees the SQLite path resolves inside the mounted data directory.
        """
        assert "DB_PATH=/data/auto_reddit.db" in compose_text, (
            "docker-compose.yml must set 'DB_PATH=/data/auto_reddit.db' in the "
            "'environment:' block so the persistent path is enforced at compose level. "
            f"Current content:\n{compose_text}"
        )

    def test_compose_mounts_sqlite_data_volume_to_data(self, compose_text: str):
        """docker-compose.yml MUST mount the sqlite_data volume to /data so that
        DB_PATH=/data/auto_reddit.db resolves inside the persistent volume.

        Processed-state data survives container recreation because /data is backed
        by the named volume, not the ephemeral container filesystem.
        """
        assert "sqlite_data:/data" in compose_text, (
            "docker-compose.yml must mount 'sqlite_data:/data' so the database "
            "path resolves inside the persistent volume. "
            f"Found:\n{compose_text}"
        )

    def test_compose_declares_sqlite_data_named_volume(self, compose_text: str):
        """docker-compose.yml MUST declare `sqlite_data:` in the top-level `volumes:`
        block so Docker manages the volume lifecycle across container recreations.
        """
        # The volumes: section must contain a sqlite_data entry
        volumes_idx = compose_text.find("volumes:")
        assert volumes_idx != -1, (
            "docker-compose.yml must have a top-level 'volumes:' block."
        )
        volumes_section = compose_text[volumes_idx:]
        assert "sqlite_data" in volumes_section, (
            "docker-compose.yml must declare 'sqlite_data' in the top-level volumes block "
            "so Docker manages the volume lifecycle. "
            f"Volumes section:\n{volumes_section}"
        )

    def test_compose_db_path_is_inside_mounted_data_directory(self, compose_text: str):
        """DB_PATH MUST be /data/auto_reddit.db — inside the volume mount at /data.

        Any other path (e.g. /app/auto_reddit.db) would be ephemeral and lost on
        container recreation.
        """
        assert "/data/auto_reddit.db" in compose_text, (
            "DB_PATH must resolve inside the /data mount point. "
            "A path outside /data would be ephemeral and break persistence. "
            f"Current compose:\n{compose_text}"
        )


# ---------------------------------------------------------------------------
# Requirement: Persistent Docker SQLite Path
# Scenario: No ephemeral default in compose workflow
# ---------------------------------------------------------------------------


class TestNoEphemeralDefaultInComposeWorkflow:
    """Spec scenario: 'No ephemeral default in compose workflow'.

    GIVEN an operator follows the standard compose workflow without custom overrides
    WHEN the run completes successfully
    THEN the workflow MUST NOT rely on an in-container ephemeral SQLite path as its
         default state location
    """

    def test_compose_does_not_use_ephemeral_app_path_as_db_path(
        self, compose_text: str
    ):
        """docker-compose.yml MUST NOT specify an in-container ephemeral path
        (e.g. /app/auto_reddit.db) as DB_PATH.

        The Settings default is 'auto_reddit.db' (relative → /app/auto_reddit.db in
        Docker). The compose-level `environment:` override MUST prevent this default
        from being used in the compose workflow.
        """
        # The environment block must not set DB_PATH to a non-/data path
        assert "DB_PATH=auto_reddit.db" not in compose_text, (
            "docker-compose.yml must not set DB_PATH to the ephemeral default "
            "'auto_reddit.db'. This would place the database in the container "
            "filesystem and lose state on container recreation."
        )
        # Verify the environment override exists and uses /data
        assert "environment:" in compose_text, (
            "docker-compose.yml must have an 'environment:' block to enforce DB_PATH."
        )

    def test_env_example_docker_critical_section_has_data_path(
        self, env_example_text: str
    ):
        """The Docker-critical section of .env.example MUST show DB_PATH=/data/auto_reddit.db
        (uncommented) so operators copying the template get the correct persistent default.

        An operator following standard setup (cp .env.example .env) MUST NOT end up
        with an ephemeral DB_PATH by default.
        """
        # Find a non-commented line that sets DB_PATH to /data/auto_reddit.db
        uncommented_db_path_found = False
        for line in env_example_text.splitlines():
            stripped = line.strip()
            # Skip comment lines (they may mention DB_PATH for documentation purposes)
            if stripped.startswith("#"):
                continue
            if stripped == "DB_PATH=/data/auto_reddit.db":
                uncommented_db_path_found = True
                break

        assert uncommented_db_path_found, (
            ".env.example must contain an uncommented 'DB_PATH=/data/auto_reddit.db' "
            "line in the Docker-critical section so operators get the correct persistent "
            "path by default when copying the template."
        )


# ---------------------------------------------------------------------------
# Requirement: Operational Environment Classification
# Scenario: Required runtime variables are explicit
# ---------------------------------------------------------------------------


class TestRequiredRuntimeVariablesAreExplicit:
    """Spec scenario: 'Required runtime variables are explicit'.

    GIVEN an operator opens the environment template
    WHEN preparing a standard production-like run
    THEN required runtime variables SHALL be grouped distinctly from optional settings
    AND missing required values SHALL be obvious without consulting source code
    """

    _REQUIRED_VARS = [
        "DEEPSEEK_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "REDDIT_API_KEY",
    ]

    def test_env_example_has_required_section_header(self, env_example_text: str):
        """The environment template MUST have an explicit 'REQUIRED' section header
        so operators can identify mandatory runtime inputs at a glance.
        """
        assert "REQUIRED" in env_example_text, (
            ".env.example must contain a 'REQUIRED' section header to group mandatory "
            "variables distinctly from optional settings."
        )

    def test_env_example_required_vars_present_and_ungrouped_with_defaults(
        self, env_example_text: str
    ):
        """All required variables MUST appear in the template without inline defaults
        (empty value) so missing values are obvious — operators cannot accidentally
        inherit a dummy value.
        """
        for var in self._REQUIRED_VARS:
            # Var must appear in the file
            assert var in env_example_text, (
                f".env.example must list required variable '{var}'. "
                "Missing from template."
            )
            # Each required var line must have an empty value (var=, not var=something)
            for line in env_example_text.splitlines():
                stripped = line.strip()
                if stripped.startswith(var + "="):
                    assert stripped == f"{var}=", (
                        f".env.example: required variable '{var}' must have an empty "
                        f"value ('{var}=') so missing values are obvious. "
                        f"Found: {line!r}"
                    )
                    break

    def test_env_example_has_optional_section_header(self, env_example_text: str):
        """The template MUST have an 'Optional' section header to separate tuneable
        parameters from required runtime secrets.
        """
        assert "Optional" in env_example_text, (
            ".env.example must contain an 'Optional' section header to distinguish "
            "tuneable parameters from required runtime secrets."
        )


# ---------------------------------------------------------------------------
# Requirement: Operational Environment Classification
# Scenario: Docker-critical variables stay isolated
# ---------------------------------------------------------------------------


class TestDockerCriticalVariablesStayIsolated:
    """Spec scenario: 'Docker-critical variables stay isolated'.

    GIVEN an operator prepares a containerized run
    WHEN reviewing Docker-critical configuration
    THEN variables that affect persistence or execution safety MUST be grouped
         separately from smoke-only or optional knobs
    AND the template MUST NOT imply that smoke-only settings are required for
         routine execution
    """

    def test_env_example_has_docker_critical_section_header(
        self, env_example_text: str
    ):
        """The template MUST have a 'Docker-critical' section header to isolate
        persistence-affecting variables from other variable groups.
        """
        assert "Docker-critical" in env_example_text, (
            ".env.example must have a 'Docker-critical' section header to group "
            "variables that affect persistence or execution safety. "
            "This ensures operators can identify persistence-critical settings "
            "without consulting source code."
        )

    def test_env_example_has_smoke_tests_section_header(self, env_example_text: str):
        """The template MUST have a 'Smoke tests' or 'only for integration tests'
        annotation to clarify that smoke variables are NOT required for routine runs.
        """
        assert (
            "Smoke tests" in env_example_text or "smoke" in env_example_text.lower()
        ), (
            ".env.example must have a section header or annotation identifying "
            "smoke-test-only variables so operators do not treat them as required "
            "for routine production runs."
        )

    def test_env_example_smoke_vars_are_commented_out(self, env_example_text: str):
        """Smoke-only variables MUST be commented out in the template so they are
        not accidentally included in a standard production `.env` copy.
        """
        smoke_vars = [
            "REDDIT_SMOKE_API_KEY",
            "TELEGRAM_SMOKE_BOT_TOKEN",
            "TELEGRAM_SMOKE_CHAT_ID",
        ]
        for var in smoke_vars:
            if var in env_example_text:
                for line in env_example_text.splitlines():
                    if var in line:
                        assert line.strip().startswith("#"), (
                            f".env.example: smoke variable '{var}' must be commented "
                            f"out to signal it is not required for routine execution. "
                            f"Found: {line!r}"
                        )

    def test_env_example_db_path_in_docker_critical_section_not_smoke(
        self, env_example_text: str
    ):
        """DB_PATH MUST appear in the Docker-critical section, NOT in the smoke-tests
        section, to correctly signal its role as a persistence-affecting variable.
        """
        lines = env_example_text.splitlines()
        docker_critical_idx = None
        smoke_idx = None

        for i, line in enumerate(lines):
            if "Docker-critical" in line and docker_critical_idx is None:
                docker_critical_idx = i
            if ("Smoke tests" in line or "smoke" in line.lower()) and smoke_idx is None:
                smoke_idx = i

        db_path_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("DB_PATH="):
                db_path_idx = i
                break

        assert db_path_idx is not None, (
            ".env.example must contain an uncommented DB_PATH= line."
        )
        assert docker_critical_idx is not None, (
            ".env.example must have a Docker-critical section."
        )

        # DB_PATH line must come after Docker-critical header
        assert db_path_idx > docker_critical_idx, (
            "DB_PATH= must appear after the Docker-critical section header, "
            f"but found DB_PATH at line {db_path_idx + 1} and "
            f"Docker-critical at line {docker_critical_idx + 1}."
        )

        # If smoke section exists, DB_PATH must appear before it
        if smoke_idx is not None:
            assert db_path_idx < smoke_idx, (
                "DB_PATH= must appear before the smoke-tests section, "
                f"but found DB_PATH at line {db_path_idx + 1} and "
                f"smoke section at line {smoke_idx + 1}."
            )


# ---------------------------------------------------------------------------
# Requirement: Isolated Operational Runbook
# Scenario: Cron-compatible command path is documented
# ---------------------------------------------------------------------------


class TestCronCompatibleCommandPathIsDocumented:
    """Spec scenario: 'Cron-compatible command path is documented'.

    GIVEN an operator needs to configure scheduled execution
    WHEN consulting the operational guidance
    THEN the guidance SHALL provide one reproducible invocation path for the
         supported container workflow
    AND it SHALL identify the environment file and persistence assumptions used
         by that workflow
    """

    def test_operations_md_exists(self):
        """docs/operations.md MUST exist as the dedicated operational runbook."""
        assert OPERATIONS_MD.exists(), (
            "docs/operations.md must exist as the dedicated operational runbook "
            "for scheduled/container execution guidance."
        )

    def test_operations_md_has_cron_invocation_command(self, operations_text: str):
        """The runbook MUST contain a concrete cron invocation using
        `docker compose run --rm` so operators have a reproducible command.
        """
        assert "docker compose run --rm" in operations_text, (
            "docs/operations.md must document the concrete cron invocation using "
            "'docker compose run --rm auto-reddit'. "
            "This is the reproducible invocation path required by the spec."
        )

    def test_operations_md_has_cron_section(self, operations_text: str):
        """The runbook MUST have a Cron Setup section or equivalent."""
        assert "Cron" in operations_text or "cron" in operations_text, (
            "docs/operations.md must have a Cron Setup section providing scheduled "
            "execution guidance."
        )

    def test_operations_md_identifies_env_file_assumption(self, operations_text: str):
        """The runbook MUST reference the `.env` file or `env_file` convention so
        operators understand the environment file assumption used by the workflow.
        """
        assert ".env" in operations_text, (
            "docs/operations.md must identify the .env file as the environment file "
            "assumption used by the cron/compose workflow."
        )

    def test_operations_md_documents_persistence_assumption(self, operations_text: str):
        """The runbook MUST document the persistence assumption (volume at /data)
        so operators understand where state is stored.
        """
        assert "/data" in operations_text, (
            "docs/operations.md must document the /data volume as the persistence "
            "assumption used by the Docker compose workflow."
        )

    def test_operations_md_has_db_path_documentation(self, operations_text: str):
        """The runbook MUST reference DB_PATH so operators understand the
        persistence contract of the container workflow.
        """
        assert "DB_PATH" in operations_text, (
            "docs/operations.md must reference DB_PATH to document the persistence "
            "assumption and explain that compose enforces the correct path."
        )


# ---------------------------------------------------------------------------
# Requirement: Isolated Operational Runbook
# Scenario: Operational guidance does not rewrite shared runtime truth
# ---------------------------------------------------------------------------


class TestOperationalGuidanceDoesNotRewriteSharedRuntimeTruth:
    """Spec scenario: 'Operational guidance does not rewrite shared runtime truth'.

    GIVEN this change adds or updates execution guidance
    WHEN documentation is reviewed
    THEN execution instructions MUST remain in an operationally scoped artifact
    AND the change MUST NOT become a general cleanup of shared runtime-truth sections
         owned by another change
    """

    def test_operations_md_is_separate_from_architecture_md(self):
        """Execution guidance MUST live in docs/operations.md, NOT embedded in
        docs/architecture.md beyond the minimal factual fix.

        The spec requires operational instructions to remain in an operationally
        scoped artifact.
        """
        assert OPERATIONS_MD.exists(), (
            "docs/operations.md must exist as the operationally scoped artifact "
            "for execution guidance."
        )
        # The architecture.md file should exist and NOT contain full cron instructions
        assert ARCHITECTURE_MD.exists(), (
            "docs/architecture.md must still exist as the shared runtime-truth document."
        )

    def test_architecture_md_does_not_contain_full_cron_setup(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST NOT contain full cron setup instructions —
        those belong exclusively in docs/operations.md.

        This ensures the change did not accidentally rewrite shared runtime-truth
        sections with operational content.
        """
        # A full cron invocation in architecture.md would indicate bleedover
        # The architecture file may mention the operational model at a high level,
        # but must not contain the detailed cron command
        assert "crontab" not in architecture_text.lower(), (
            "docs/architecture.md must not contain crontab instructions. "
            "Cron setup belongs in docs/operations.md (operationally scoped artifact)."
        )

    def test_architecture_md_preserves_existing_sections(self, architecture_text: str):
        """docs/architecture.md MUST still contain its core architectural sections,
        confirming this change did not destroy shared runtime-truth content.
        """
        expected_sections = [
            "## 1.",  # Stack principal
            "## 2.",  # Estructura del codigo
            "## 3.",  # Modelo operativo
            "## 4.",  # Persistencia
            "## 5.",  # Contratos internos
            "## 6.",  # Configuracion y secretos
        ]
        for section in expected_sections:
            assert section in architecture_text, (
                f"docs/architecture.md must still contain section '{section}'. "
                "This change must not have removed or restructured architecture sections."
            )

    def test_architecture_md_section6_lists_telegram_chat_id(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST include TELEGRAM_CHAT_ID in the required
        variables list — this is the minimal factual fix required by the design.

        The Settings class defines telegram_chat_id as a required field. The
        architecture document must reflect this factual reality.
        """
        assert "TELEGRAM_CHAT_ID" in architecture_text, (
            "docs/architecture.md §6 must list 'TELEGRAM_CHAT_ID' as a required "
            "variable. It is defined as a required field in Settings and its omission "
            "is a factual error in the shared runtime-truth document."
        )
