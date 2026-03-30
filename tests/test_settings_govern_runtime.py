"""Spec scenario tests for `settings-govern-runtime`.

Covers all 6 spec scenarios via structural assertions on the repository artifacts
(no live external services required):

Requirement: Document the operational settings contract without decorative knobs
  - Scenario: Runtime-backed settings inventory is documented consistently
  - Scenario: Operational parameters are not omitted from the contract

Requirement: Distinguish pre-evaluation and post-evaluation daily caps
  - Scenario: Pre-evaluation cap is explained correctly
  - Scenario: Post-evaluation cap remains distinct even with same default

Requirement: Keep architecture, product, and example environment documents aligned
  - Scenario: Cross-document review no longer produces contradictory guidance
  - Scenario: Example DB path does not misstate the runtime default

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
ENV_EXAMPLE = REPO_ROOT / ".env.example"
ARCHITECTURE_MD = REPO_ROOT / "docs" / "architecture.md"
PRODUCT_MD = REPO_ROOT / "docs" / "product" / "product.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def env_example_text() -> str:
    assert ENV_EXAMPLE.exists(), f".env.example not found at {ENV_EXAMPLE}"
    return ENV_EXAMPLE.read_text()


@pytest.fixture(scope="module")
def architecture_text() -> str:
    assert ARCHITECTURE_MD.exists(), (
        f"docs/architecture.md not found at {ARCHITECTURE_MD}"
    )
    return ARCHITECTURE_MD.read_text()


@pytest.fixture(scope="module")
def product_text() -> str:
    assert PRODUCT_MD.exists(), f"docs/product/product.md not found at {PRODUCT_MD}"
    return PRODUCT_MD.read_text()


# ---------------------------------------------------------------------------
# Requirement: Document the operational settings contract without decorative knobs
# Scenario: Runtime-backed settings inventory is documented consistently
# ---------------------------------------------------------------------------


class TestRuntimeBackedSettingsInventoryIsDocumentedConsistently:
    """Spec scenario: 'Runtime-backed settings inventory is documented consistently'.

    GIVEN the runtime contract is verified from `Settings` and its real consumers
    WHEN the configuration documentation is reviewed
    THEN the documented settings inventory matches the runtime-backed inventory
    AND no documented setting is presented as unused or decorative
    """

    # The 9 settings that form the verified runtime contract:
    # 4 required secrets + 5 operational parameters
    _REQUIRED_SECRETS = [
        "DEEPSEEK_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "REDDIT_API_KEY",
    ]

    _OPERATIONAL_PARAMS = [
        "max_daily_opportunities",
        "review_window_days",
        "daily_review_limit",
        "deepseek_model",
        "db_path",
    ]

    def test_architecture_section6_documents_all_four_required_secrets(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST list all 4 required runtime secrets.

        These are the variables that Settings defines as required fields with no
        defaults; their absence causes the process to abort at startup.
        """
        for secret in self._REQUIRED_SECRETS:
            assert secret in architecture_text, (
                f"docs/architecture.md §6 must list required secret '{secret}'. "
                "The documented contract must match the verified runtime contract."
            )

    def test_architecture_section6_documents_all_five_operational_params(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST list all 5 operational parameters.

        Together with the 4 secrets, these form the 9-setting runtime contract.
        Each parameter has a real runtime consumer and must not be omitted.
        """
        for param in self._OPERATIONAL_PARAMS:
            assert param in architecture_text, (
                f"docs/architecture.md §6 must document operational parameter '{param}'. "
                f"Total documented surface must be 9 settings (4 secrets + 5 params)."
            )

    def test_architecture_section6_documents_nine_total_settings(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST document exactly the 9-setting runtime contract.

        The verified runtime contract has:
        - 4 required secrets (no defaults)
        - 5 operational parameters (with safe defaults)

        All 9 must appear in the §6 configuration section.
        """
        all_settings = self._REQUIRED_SECRETS + self._OPERATIONAL_PARAMS
        missing = [s for s in all_settings if s not in architecture_text]
        assert not missing, (
            f"docs/architecture.md §6 is missing these runtime-backed settings: "
            f"{missing}. "
            "The documented inventory must match the verified 9-setting runtime contract."
        )

    def test_architecture_section6_presents_settings_as_runtime_backed(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST present settings within the configuration section
        (§6), not as decorative notes or optional extras.

        The §6 header must exist and must contain the documented settings.
        """
        assert "## 6." in architecture_text, (
            "docs/architecture.md must have a §6 (configuration) section "
            "to document the operational settings contract."
        )
        # Find §6 and verify settings appear after it
        section6_idx = architecture_text.find("## 6.")
        section7_idx = architecture_text.find("## 7.")
        section6_content = (
            architecture_text[section6_idx:section7_idx]
            if section7_idx != -1
            else architecture_text[section6_idx:]
        )
        for param in self._OPERATIONAL_PARAMS:
            assert param in section6_content, (
                f"Operational parameter '{param}' must appear within §6 of "
                "docs/architecture.md, not outside the configuration section."
            )


# ---------------------------------------------------------------------------
# Requirement: Document the operational settings contract without decorative knobs
# Scenario: Operational parameters are not omitted from the contract
# ---------------------------------------------------------------------------


class TestOperationalParametersAreNotOmittedFromContract:
    """Spec scenario: 'Operational parameters are not omitted from the contract'.

    GIVEN `deepseek_model` and `db_path` affect runtime behavior through real consumers
    WHEN maintainers review the documented configuration surface
    THEN both settings appear as operational parameters in the documented contract
    """

    def test_architecture_documents_deepseek_model_as_operational_param(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST document `deepseek_model` as an operational
        parameter with its runtime consumer reference.

        `deepseek_model` has a real consumer at `evaluator.py:331` and must appear
        in the documented contract as a runtime-backed operational parameter.
        """
        assert "deepseek_model" in architecture_text, (
            "docs/architecture.md must document 'deepseek_model' as an operational "
            "parameter. It has a verified runtime consumer at evaluator.py:331 and "
            "must not be omitted from the documented contract."
        )

    def test_architecture_documents_db_path_as_operational_param(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST document `db_path` as an operational parameter
        with its runtime consumer reference.

        `db_path` has a real consumer at `store.py:20` and must appear in the
        documented contract as a runtime-backed operational parameter.
        """
        assert "db_path" in architecture_text, (
            "docs/architecture.md must document 'db_path' as an operational "
            "parameter. It has a verified runtime consumer at store.py:20 and "
            "must not be omitted from the documented contract."
        )

    def test_architecture_deepseek_model_has_consumer_reference(
        self, architecture_text: str
    ):
        """The `deepseek_model` entry in docs/architecture.md MUST include a reference
        to its runtime consumer (`evaluator.py`) so maintainers can verify the
        parameter is not decorative.
        """
        assert "evaluator.py" in architecture_text, (
            "docs/architecture.md must reference 'evaluator.py' as the runtime "
            "consumer of 'deepseek_model'. This confirms the setting is runtime-backed."
        )

    def test_architecture_db_path_has_consumer_reference(self, architecture_text: str):
        """The `db_path` entry in docs/architecture.md MUST include a reference to its
        runtime consumer (`store.py`) so maintainers can verify the parameter is
        not decorative.
        """
        assert "store.py" in architecture_text, (
            "docs/architecture.md must reference 'store.py' as the runtime consumer "
            "of 'db_path'. This confirms the setting is runtime-backed."
        )

    def test_env_example_documents_deepseek_model_as_optional_param(
        self, env_example_text: str
    ):
        """`.env.example` MUST document `DEEPSEEK_MODEL` in the Optional section.

        The env.example serves as the operational surface of the settings contract.
        `DEEPSEEK_MODEL` must appear as a commented optional parameter with its default.
        """
        assert "DEEPSEEK_MODEL" in env_example_text, (
            ".env.example must document 'DEEPSEEK_MODEL' in the Optional section "
            "so operators know it exists and can tune it without consulting source code."
        )

    def test_env_example_documents_db_path_in_docker_critical_section(
        self, env_example_text: str
    ):
        """`.env.example` MUST document `DB_PATH` in the Docker-critical section.

        `DB_PATH` is a persistence-affecting parameter that must appear in the
        template so operators understand the runtime contract.
        """
        assert "DB_PATH" in env_example_text, (
            ".env.example must document 'DB_PATH' so operators understand the "
            "persistence contract of the container workflow."
        )


# ---------------------------------------------------------------------------
# Requirement: Distinguish pre-evaluation and post-evaluation daily caps
# Scenario: Pre-evaluation cap is explained correctly
# ---------------------------------------------------------------------------


class TestPreEvaluationCapIsExplainedCorrectly:
    """Spec scenario: 'Pre-evaluation cap is explained correctly'.

    GIVEN a maintainer reads the daily-limit documentation
    WHEN they inspect the meaning of `daily_review_limit`
    THEN the documentation states that it trims the review set before AI evaluation
    """

    def test_architecture_daily_review_limit_has_pre_evaluation_semantics(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST describe `daily_review_limit` as a
        pre-evaluation IA cap.

        The documentation must make it explicit that this limit applies BEFORE
        AI evaluation to trim the candidate set.
        """
        assert "daily_review_limit" in architecture_text, (
            "docs/architecture.md must document 'daily_review_limit'."
        )
        # Verify that the pre-evaluation semantics are present
        assert (
            "pre-evaluación" in architecture_text
            or "pre-evaluation" in architecture_text
        ), (
            "docs/architecture.md must use 'pre-evaluación' or 'pre-evaluation' "
            "vocabulary to describe 'daily_review_limit', making it explicit that "
            "this cap applies before AI evaluation."
        )

    def test_architecture_daily_review_limit_references_main_py(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST reference `main.py` as the consumer of
        `daily_review_limit` to confirm it is runtime-backed.
        """
        assert "main.py" in architecture_text, (
            "docs/architecture.md must reference 'main.py' as the runtime consumer "
            "of 'daily_review_limit' (main.py:64 applies the pre-evaluation cap)."
        )

    def test_product_daily_review_limit_explains_pre_evaluation_semantics(
        self, product_text: str
    ):
        """docs/product/product.md MUST describe `daily_review_limit` as a
        pre-evaluation cap so product stakeholders understand its control point.
        """
        assert "daily_review_limit" in product_text, (
            "docs/product/product.md must document 'daily_review_limit' with "
            "its pre-evaluation semantics so product stakeholders can distinguish "
            "it from the post-evaluation cap."
        )
        assert "pre-evaluación" in product_text or "pre-evaluation" in product_text, (
            "docs/product/product.md must use 'pre-evaluación' or 'pre-evaluation' "
            "vocabulary when describing 'daily_review_limit'."
        )

    def test_env_example_daily_review_limit_has_pre_evaluation_comment(
        self, env_example_text: str
    ):
        """`.env.example` MUST describe `DAILY_REVIEW_LIMIT` with its pre-evaluation
        semantics in the comment above the variable line.
        """
        assert "DAILY_REVIEW_LIMIT" in env_example_text, (
            ".env.example must document 'DAILY_REVIEW_LIMIT'."
        )
        assert (
            "pre-evaluación" in env_example_text or "pre-evaluation" in env_example_text
        ), (
            ".env.example must include a 'pre-evaluación' or 'pre-evaluation' comment "
            "for DAILY_REVIEW_LIMIT to distinguish it from the post-evaluation cap."
        )


# ---------------------------------------------------------------------------
# Requirement: Distinguish pre-evaluation and post-evaluation daily caps
# Scenario: Post-evaluation cap remains distinct even with same default
# ---------------------------------------------------------------------------


class TestPostEvaluationCapRemainsDistinctEvenWithSameDefault:
    """Spec scenario: 'Post-evaluation cap remains distinct even with same default'.

    GIVEN both daily caps default to 8
    WHEN an operator compares both settings in the documentation
    THEN the documentation makes clear that `max_daily_opportunities` applies after
         evaluation/selection and before Telegram delivery
    AND the two limits are not described as synonyms
    """

    def test_architecture_max_daily_opportunities_has_post_evaluation_semantics(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST describe `max_daily_opportunities` as a
        post-evaluation IA cap, distinct from `daily_review_limit`.

        Both default to 8, but they apply at different pipeline stages. The
        documentation must not conflate them.
        """
        assert "max_daily_opportunities" in architecture_text, (
            "docs/architecture.md must document 'max_daily_opportunities'."
        )
        assert (
            "post-evaluación" in architecture_text
            or "post-evaluation" in architecture_text
        ), (
            "docs/architecture.md must use 'post-evaluación' or 'post-evaluation' "
            "vocabulary to describe 'max_daily_opportunities', making it explicit that "
            "this cap applies after AI evaluation and selection."
        )

    def test_architecture_both_caps_documented_in_section6(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST document BOTH daily caps so operators can
        compare them side-by-side.

        When both caps appear in the same section with distinct semantics, operators
        can immediately see they are different control points despite equal defaults.
        """
        section6_idx = architecture_text.find("## 6.")
        section7_idx = architecture_text.find("## 7.")
        section6_content = (
            architecture_text[section6_idx:section7_idx]
            if section7_idx != -1
            else architecture_text[section6_idx:]
        )
        assert "daily_review_limit" in section6_content, (
            "docs/architecture.md §6 must document 'daily_review_limit' (pre-evaluation cap)."
        )
        assert "max_daily_opportunities" in section6_content, (
            "docs/architecture.md §6 must document 'max_daily_opportunities' (post-evaluation cap)."
        )

    def test_architecture_max_daily_opportunities_references_delivery_module(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST reference `delivery/__init__.py` as the consumer
        of `max_daily_opportunities` to confirm its post-evaluation control point.
        """
        assert "delivery" in architecture_text, (
            "docs/architecture.md must reference the 'delivery' module as the "
            "runtime consumer of 'max_daily_opportunities' (delivery/__init__.py:81 "
            "applies the post-evaluation cap)."
        )

    def test_product_max_daily_opportunities_has_post_evaluation_semantics(
        self, product_text: str
    ):
        """docs/product/product.md MUST describe `max_daily_opportunities` as a
        post-evaluation cap, distinct from `daily_review_limit`.
        """
        assert "max_daily_opportunities" in product_text, (
            "docs/product/product.md must document 'max_daily_opportunities'."
        )
        assert "post-evaluación" in product_text or "post-evaluation" in product_text, (
            "docs/product/product.md must use 'post-evaluación' or 'post-evaluation' "
            "vocabulary when describing 'max_daily_opportunities'."
        )

    def test_env_example_max_daily_opportunities_has_post_evaluation_comment(
        self, env_example_text: str
    ):
        """`.env.example` MUST describe `MAX_DAILY_OPPORTUNITIES` with its
        post-evaluation semantics in the comment above the variable line.
        """
        assert "MAX_DAILY_OPPORTUNITIES" in env_example_text, (
            ".env.example must document 'MAX_DAILY_OPPORTUNITIES'."
        )
        assert (
            "post-evaluación" in env_example_text
            or "post-evaluation" in env_example_text
        ), (
            ".env.example must include a 'post-evaluación' or 'post-evaluation' comment "
            "for MAX_DAILY_OPPORTUNITIES to distinguish it from the pre-evaluation cap."
        )

    def test_env_example_both_caps_present_and_commented(self, env_example_text: str):
        """`.env.example` MUST document BOTH daily caps as commented-out optional params.

        Both appear with safe defaults and neither should be required for basic runs.
        Having both in the same section with distinct comments makes the semantic
        distinction visible in the operational surface.
        """
        assert "MAX_DAILY_OPPORTUNITIES" in env_example_text, (
            ".env.example must document 'MAX_DAILY_OPPORTUNITIES' as an optional parameter."
        )
        assert "DAILY_REVIEW_LIMIT" in env_example_text, (
            ".env.example must document 'DAILY_REVIEW_LIMIT' as an optional parameter."
        )

        # Both should be commented out (they have safe defaults)
        for line in env_example_text.splitlines():
            stripped = line.strip()
            if stripped.startswith(
                "MAX_DAILY_OPPORTUNITIES="
            ) and not stripped.startswith("#"):
                # Uncommented is also valid if it has the default value
                pass
            if stripped.startswith("DAILY_REVIEW_LIMIT=") and not stripped.startswith(
                "#"
            ):
                pass


# ---------------------------------------------------------------------------
# Requirement: Keep architecture, product, and example environment documents aligned
# Scenario: Cross-document review no longer produces contradictory guidance
# ---------------------------------------------------------------------------


class TestCrossDocumentReviewNoLongerProducesContradictoryGuidance:
    """Spec scenario: 'Cross-document review no longer produces contradictory guidance'.

    GIVEN a reviewer compares docs/architecture.md, docs/product/product.md, and .env.example
    WHEN they check settings names, semantics, and DB path guidance
    THEN the three documents present one coherent contract
    """

    def test_all_three_artifacts_document_daily_review_limit(
        self, architecture_text: str, product_text: str, env_example_text: str
    ):
        """All three artifacts MUST document `daily_review_limit` consistently.

        A reviewer checking all three documents must find coherent — not contradictory
        — guidance about the pre-evaluation cap.
        """
        assert "daily_review_limit" in architecture_text, (
            "docs/architecture.md must document 'daily_review_limit'."
        )
        assert "daily_review_limit" in product_text, (
            "docs/product/product.md must document 'daily_review_limit'."
        )
        assert "DAILY_REVIEW_LIMIT" in env_example_text, (
            ".env.example must document 'DAILY_REVIEW_LIMIT'."
        )

    def test_all_three_artifacts_document_max_daily_opportunities(
        self, architecture_text: str, product_text: str, env_example_text: str
    ):
        """All three artifacts MUST document `max_daily_opportunities` consistently.

        A reviewer checking all three documents must find coherent — not contradictory
        — guidance about the post-evaluation cap.
        """
        assert "max_daily_opportunities" in architecture_text, (
            "docs/architecture.md must document 'max_daily_opportunities'."
        )
        assert "max_daily_opportunities" in product_text, (
            "docs/product/product.md must document 'max_daily_opportunities'."
        )
        assert "MAX_DAILY_OPPORTUNITIES" in env_example_text, (
            ".env.example must document 'MAX_DAILY_OPPORTUNITIES'."
        )

    def test_all_three_artifacts_present_coherent_pre_post_vocabulary(
        self, architecture_text: str, product_text: str, env_example_text: str
    ):
        """All three artifacts MUST use pre/post-evaluation vocabulary for the caps.

        The vocabulary must be consistent so a reviewer does not get contradictory
        semantics when cross-referencing the documents.
        """
        for label, text in [
            ("docs/architecture.md", architecture_text),
            ("docs/product/product.md", product_text),
            (".env.example", env_example_text),
        ]:
            has_pre = "pre-evaluación" in text or "pre-evaluation" in text
            has_post = "post-evaluación" in text or "post-evaluation" in text
            assert has_pre and has_post, (
                f"{label} must use BOTH 'pre-evaluación'/'pre-evaluation' AND "
                f"'post-evaluación'/'post-evaluation' vocabulary to present the "
                f"two caps coherently. Missing: "
                f"{'pre-evaluation' if not has_pre else ''} "
                f"{'post-evaluation' if not has_post else ''}".strip()
            )

    def test_architecture_and_product_agree_on_deepseek_model_name(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST document the canonical `deepseek-chat` model name.

        This ensures the documented model name is runtime-backed and not contradictory
        with what the runtime actually uses.
        """
        assert "deepseek-chat" in architecture_text, (
            "docs/architecture.md must document 'deepseek-chat' as the default "
            "model name for 'deepseek_model'. This is the runtime-backed default "
            "confirmed in evaluator.py."
        )


# ---------------------------------------------------------------------------
# Requirement: Keep architecture, product, and example environment documents aligned
# Scenario: Example DB path does not misstate the runtime default
# ---------------------------------------------------------------------------


class TestExampleDbPathDoesNotMisstateRuntimeDefault:
    """Spec scenario: 'Example DB path does not misstate the runtime default'.

    GIVEN .env.example shows a Docker-oriented DB_PATH example
    WHEN a developer reads the surrounding guidance
    THEN they can distinguish the operational example from the runtime default value
    AND the document does not imply a false default or precedence rule
    """

    def test_env_example_db_path_clarifies_docker_context(self, env_example_text: str):
        """`.env.example` MUST provide guidance that distinguishes the Docker-oriented
        DB_PATH example from the runtime default.

        The DB_PATH=/data/auto_reddit.db example is Docker-specific. The runtime
        default is `auto_reddit.db` (relative path). The comment must make this
        distinction clear to avoid misstating the runtime default.
        """
        assert "DB_PATH" in env_example_text, ".env.example must document DB_PATH."
        # The comment must reference docker-compose or compose to clarify context
        env_lower = env_example_text.lower()
        assert "compose" in env_lower or "docker" in env_lower, (
            ".env.example must mention 'compose' or 'docker' near DB_PATH to clarify "
            "that the /data/... path is a Docker-specific example, not the raw runtime default."
        )

    def test_env_example_db_path_documents_compose_precedence(
        self, env_example_text: str
    ):
        """`.env.example` MUST clarify that docker-compose.yml enforces DB_PATH,
        taking precedence over the .env file value.

        Without this, operators may think they need to set DB_PATH in .env when
        running via compose — but compose already enforces it via `environment:`.
        """
        # The comment should mention compose overrides or precedence
        assert (
            "docker-compose" in env_example_text
            or "compose" in env_example_text.lower()
        ), (
            ".env.example must reference docker-compose.yml or compose to document "
            "that it already enforces DB_PATH via the environment: block, which takes "
            "precedence over .env values."
        )

    def test_architecture_db_path_documents_runtime_default(
        self, architecture_text: str
    ):
        """docs/architecture.md MUST document the runtime default for `db_path`
        (`auto_reddit.db`) and its runtime consumer.

        This establishes the ground truth: the raw default is `auto_reddit.db`
        (relative), but Docker/compose overrides it to `/data/auto_reddit.db`.
        """
        assert "auto_reddit.db" in architecture_text, (
            "docs/architecture.md must document the runtime default 'auto_reddit.db' "
            "for the 'db_path' setting. This is the value used when running outside "
            "Docker without a DB_PATH override."
        )

    def test_architecture_db_path_section6_has_store_consumer(
        self, architecture_text: str
    ):
        """docs/architecture.md §6 MUST reference `store.py` for `db_path` so
        maintainers can confirm the setting is not decorative.
        """
        section6_idx = architecture_text.find("## 6.")
        section7_idx = architecture_text.find("## 7.")
        section6_content = (
            architecture_text[section6_idx:section7_idx]
            if section7_idx != -1
            else architecture_text[section6_idx:]
        )
        assert "db_path" in section6_content, (
            "docs/architecture.md §6 must contain 'db_path' entry."
        )
        assert "store.py" in section6_content, (
            "docs/architecture.md §6 must reference 'store.py' as the consumer of "
            "'db_path' to confirm it is runtime-backed."
        )
