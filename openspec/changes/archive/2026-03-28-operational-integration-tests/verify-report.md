# Verification Report

**Change**: operational-integration-tests  
**Mode**: hybrid  
**Date**: 2026-03-28 (final re-verify after corrective apply)

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 10 |
| Tasks complete | 10 |
| Tasks incomplete | 0 |

All checklist items in `openspec/changes/operational-integration-tests/tasks.md` are marked complete.

---

## Build & Tests Execution

**Build**: ➖ Skipped / not configured  
`openspec/config.yaml` does not define `rules.verify.build_command`, and workspace guidance says not to build after changes.

**Full suite**: ✅ 270 passed / ❌ 0 failed / ⚠️ 0 skipped

```text
$ uv run pytest tests/ -x --tb=short
============================== 270 passed in 28.28s ==============================
```

**Integration suite**: ✅ 11 passed / ❌ 0 failed / ⚠️ 0 skipped

```text
$ uv run pytest tests/test_integration/test_operational.py -vv --tb=short
tests/test_integration/test_operational.py::TestRetryWithoutAIReEvaluation::test_retry_uses_persisted_data_without_ai_call PASSED
tests/test_integration/test_operational.py::TestRetryWithoutAIReEvaluation::test_retry_does_not_call_evaluate_batch_even_if_new_candidates_zero PASSED
tests/test_integration/test_operational.py::TestDeliveryBoundaryIsolation::test_delivery_reads_only_persisted_records_no_upstream_reentry PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_evaluation_boundary_no_delivery_side_effect_on_rejection PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_evaluation_accepted_outcome_persisted_before_delivery_phase PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_rejected_post_stored_without_delivery_side_effect PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_run1_persists_sent_and_rejected_correctly PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_run2_excludes_sent_and_rejected_processes_new PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_pending_delivery_retry_excluded_from_decided_set PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_pending_delivery_retried_without_ai_call_in_run2 PASSED
tests/test_integration/test_operational.py::TestRedditSmokeOptional::test_real_reddit_collect_candidates_returns_nonempty_list PASSED
============================== 11 passed in 11.56s ================================
```

**Integration suite**: ✅ 10 passed / ❌ 0 failed / ⚠️ 1 skipped

```text
$ uv run pytest tests/test_integration/test_operational.py -vv --tb=short
tests/test_integration/test_operational.py::TestRetryWithoutAIReEvaluation::test_retry_uses_persisted_data_without_ai_call PASSED
tests/test_integration/test_operational.py::TestRetryWithoutAIReEvaluation::test_retry_does_not_call_evaluate_batch_even_if_new_candidates_zero PASSED
tests/test_integration/test_operational.py::TestDeliveryBoundaryIsolation::test_delivery_reads_only_persisted_records_no_upstream_reentry PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_evaluation_boundary_no_delivery_side_effect_on_rejection PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_evaluation_accepted_outcome_persisted_before_delivery_phase PASSED
tests/test_integration/test_operational.py::TestEvaluationBoundaryIsolation::test_rejected_post_stored_without_delivery_side_effect PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_run1_persists_sent_and_rejected_correctly PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_run2_excludes_sent_and_rejected_processes_new PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_pending_delivery_retry_excluded_from_decided_set PASSED
tests/test_integration/test_operational.py::TestMultiRunMemoryBoundaries::test_pending_delivery_retried_without_ai_call_in_run2 PASSED
tests/test_integration/test_operational.py::TestRedditSmokeOptional::test_real_reddit_collect_candidates_returns_nonempty_list SKIPPED
======================== 10 passed, 1 skipped in 0.70s =========================
```

**Coverage**: ➖ Not configured

---

## Previous Partial Findings Re-check

| Previous finding | Status | Evidence |
|------------------|--------|----------|
| P1 retry proof needed to demonstrate persisted `opportunity_data` reuse, not only successful send | ✅ Resolved | `test_retry_uses_persisted_data_without_ai_call` now asserts Telegram output contains `retry_post_1`, which can only come from deserializing stored opportunity JSON. |
| P3 evaluation-isolation proof needed a strict no-delivery-side-effect assertion | ✅ Resolved | `test_evaluation_boundary_no_delivery_side_effect_on_rejection` patches `auto_reddit.delivery.send_message` as a raising sentinel and passes. |
| Design doc used the wrong Telegram patch target | ✅ Resolved | `design.md` now documents `auto_reddit.delivery.send_message` and explains the import-binding reason. |

---

## Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Prove retry reuse from persisted accepted records | Retry delivery without AI re-evaluation | `::TestRetryWithoutAIReEvaluation::test_retry_uses_persisted_data_without_ai_call` | ✅ COMPLIANT |
| Prove delivery stays inside the delivery boundary | Delivery processes retries without upstream re-entry | `::TestDeliveryBoundaryIsolation::test_delivery_reads_only_persisted_records_no_upstream_reentry` | ✅ COMPLIANT |
| Prove evaluation stays isolated from Reddit and delivery side effects | Evaluation executes without delivery or Reddit side effects | `::TestEvaluationBoundaryIsolation::test_evaluation_boundary_no_delivery_side_effect_on_rejection` | ✅ COMPLIANT |
| Prove multi-run operational memory boundaries | Final decisions exclude later review while retry records remain eligible | `::TestMultiRunMemoryBoundaries::test_run2_excludes_sent_and_rejected_processes_new` + `::test_pending_delivery_retried_without_ai_call_in_run2` | ✅ COMPLIANT |
| Keep operational, unit, and smoke-test boundaries explicit | Optional smoke coverage does not block standard verification | `::TestRedditSmokeOptional::test_real_reddit_collect_candidates_returns_nonempty_list` | ✅ COMPLIANT (passes with `.env` loaded) |
| Smoke test env gate uses fallback | `REDDIT_SMOKE_API_KEY` preferred, falls back to `REDDIT_API_KEY` | Post-archive correction applied | ✅ COMPLIANT |
| Smoke test loads `.env` explicitly | `load_dotenv()` ensures env vars are available for manual/local runs | Post-archive correction: `python-dotenv` added to dev deps + `load_dotenv()` call | ✅ COMPLIANT |

**Compliance summary**: 6/6 scenarios compliant, 0 partial, 0 failing, 0 untested.

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| Retry reuse from persisted accepted records | ✅ Implemented | `main.run()` always calls `evaluate_batch(thread_contexts, settings)`, but the retry record never enters `thread_contexts`; persisted JSON is deserialized in `deliver_daily()` and rendered to Telegram. |
| Delivery stays inside delivery boundary | ✅ Implemented | `main.run()` unconditionally traverses the full pipeline; upstream boundaries are patched to return empty/controlled results so no collection, extraction, AI evaluation, or publishing side effect occurs. Delivery reads only the pre-inserted `pending_delivery` records. Spec and task wording now reflect this controlled-empty-input proof strategy as the accepted approach (no production refactoring required). |
| Evaluation stays isolated from Reddit and delivery side effects | ✅ Implemented | Rejected-path proof uses a strict Telegram sentinel and confirms `rejected` persistence without delivery. |
| Multi-run operational memory boundaries | ✅ Implemented | Real SQLite state plus `get_decided_post_ids()` proves only `sent`/`rejected` are excluded while `pending_delivery` remains retryable. |
| Operational/unit/smoke boundaries explicit | ✅ Implemented | Coverage is isolated in `tests/test_integration/`; smoke test is env-gated with `REDDIT_SMOKE_API_KEY` (fallback `REDDIT_API_KEY`) and skipped by default. `.env` is loaded via `python-dotenv` for manual/local runs. |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Patch at caller namespace | ✅ Yes | `auto_reddit.main.*` is used for orchestration boundaries; Telegram patch target is `auto_reddit.delivery.send_message`, matching the corrected design note. |
| Real `CandidateStore` + `tmp_path` SQLite | ✅ Yes | Tests use real SQLite files and `CandidateStore.init_db()`. |
| Shared helper pattern | ✅ Yes | `_make_opportunity_json`, `_make_settings`, `_make_candidate`, `_make_thread_context` centralize fixtures. |
| Pytest fixtures, no `TestCase` | ✅ Yes | Test module uses pytest fixtures/classes only. |
| Env-gated smoke tests | ✅ Yes | `_SMOKE_API_KEY = os.getenv("REDDIT_SMOKE_API_KEY") or os.getenv("REDDIT_API_KEY")` used in both `skipif` and test body. Prefers dedicated smoke key, falls back to general Reddit key. `python-dotenv` `load_dotenv()` ensures `.env` is loaded for manual runs. |
| Deterministic time | ✅ Yes | Operational tests patch `time.time` to `_FIXED_EPOCH`. |

---

## Issues Found

**CRITICAL**

None.

**WARNING**

None.

---

## Verdict

**PASS**

All six spec scenarios are now compliant. The corrective apply resolved all three previous partial findings. The final artifact-alignment pass reconciled P2 wording with the accepted controlled-empty-input proof strategy (`main.run()` always traverses the full pipeline; no production refactoring required). Post-archive correction added explicit `.env` loading via `python-dotenv` so the smoke test runs on manual/local execution without requiring pre-sourced env vars. Full runtime evidence: `270 passed, 0 skipped`.
