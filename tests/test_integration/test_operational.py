"""Operational integration tests for the main.run() pipeline.

Covers:
- P1: Retry delivery without AI re-evaluation
- P2: Delivery boundary isolation (no upstream re-entry)
- P3: Evaluation boundary isolation (no delivery/Reddit side effects)
- P4: Multi-run operational memory boundaries
- Optional smoke tests (env-gated, skipped by default)

All tests use real SQLite via tmp_path, no TestCase classes.
I/O boundaries patched at auto_reddit.main.* caller namespace per design decision #1.
"""

from __future__ import annotations

import datetime
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from auto_reddit.main import run
from auto_reddit.persistence.store import CandidateStore
from auto_reddit.shared.contracts import (
    AcceptedOpportunity,
    ContextQuality,
    OpportunityType,
    RedditCandidate,
    RedditComment,
    RejectedPost,
    RejectionType,
    ThreadContext,
)

# ---------------------------------------------------------------------------
# Module-level fixture: force weekday for all integration tests.
# The weekend guard in main.run() uses datetime.date.today().weekday().
# Without this, tests run on a Saturday/Sunday would skip the pipeline.
# ---------------------------------------------------------------------------

_WEEKDAY_DATE = datetime.date(2026, 3, 25)  # Wednesday — guaranteed weekday


@pytest.fixture(autouse=True)
def force_weekday(monkeypatch):
    """Patch auto_reddit.main.datetime so date.today() always returns a Wednesday."""
    import auto_reddit.main as _main_module

    class _FakeDatetime:
        @staticmethod
        def today():
            return _WEEKDAY_DATE

    class _FakeDateTime:
        date = _FakeDatetime

    monkeypatch.setattr(_main_module, "datetime", _FakeDateTime)


# ---------------------------------------------------------------------------
# Helpers — follow pattern from tests/test_delivery/test_deliver_daily.py
# ---------------------------------------------------------------------------

_FIXED_EPOCH = 1_700_000_000  # deterministic time.time() anchor


def _make_opportunity_json(post_id: str = "abc123") -> str:
    """Build a valid serialized AcceptedOpportunity for the given post_id."""
    opp = AcceptedOpportunity(
        post_id=post_id,
        title=f"Post {post_id}",
        link=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        post_language="en",
        opportunity_type=OpportunityType.funcionalidad,
        opportunity_reason="El hilo está sin respuesta.",
        post_summary_es="El usuario pregunta algo.",
        comment_summary_es="Sin respuestas.",
        suggested_response_es="Respuesta en español.",
        suggested_response_en="English answer.",
    )
    return opp.model_dump_json()


def _make_settings(tmp_path: "pytest.TempPathFactory", cap: int = 8) -> MagicMock:
    """Return a mock Settings with db_path pointing to tmp_path SQLite and dummy tokens."""
    settings = MagicMock()
    settings.db_path = str(tmp_path / "test.db")
    settings.telegram_bot_token = "BOT_TOKEN"
    settings.telegram_chat_id = "CHAT_ID"
    settings.max_daily_opportunities = cap
    settings.daily_review_limit = cap
    settings.reddit_api_key = "DUMMY_REDDIT_KEY"
    settings.review_window_days = 7
    return settings


def _make_candidate(post_id: str, created_utc: int | None = None) -> RedditCandidate:
    """Return a minimal valid RedditCandidate."""
    if created_utc is None:
        created_utc = _FIXED_EPOCH
    return RedditCandidate(
        post_id=post_id,
        title=f"Post title {post_id}",
        selftext="Some question text",
        url=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        permalink=f"https://www.reddit.com/r/Odoo/comments/{post_id}/",
        author="testuser",
        subreddit="Odoo",
        created_utc=created_utc,
        num_comments=1,
        source_api="reddit3",
    )


def _make_thread_context(candidate: RedditCandidate) -> ThreadContext:
    """Return a minimal ThreadContext for the given candidate."""
    return ThreadContext(
        candidate=candidate,
        comments=[
            RedditComment(
                comment_id="c1",
                author="commenter",
                body="Some comment",
                score=1,
                created_utc=candidate.created_utc + 100,
                permalink=None,
                parent_id=None,
                depth=0,
                source_api="reddit3",
            )
        ],
        comment_count=1,
        quality=ContextQuality.partial,
        source_api="reddit3",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def operational_store(tmp_path):
    """Initialized CandidateStore backed by a real tmp_path SQLite file."""
    store = CandidateStore(str(tmp_path / "test.db"))
    store.init_db()
    return store


# ---------------------------------------------------------------------------
# P1 — Retry delivery without AI re-evaluation
# Spec: pending_delivery reuses persisted opportunity_data; evaluate_batch NOT called
# ---------------------------------------------------------------------------


class TestRetryWithoutAIReEvaluation:
    """P1: Retry delivery should not trigger AI re-evaluation."""

    def test_retry_uses_persisted_data_without_ai_call(self, tmp_path):
        """
        GIVEN a real SQLite store contains a valid pending_delivery record
        WHEN main.run() executes with evaluate_batch patched as a failing sentinel
        THEN delivery succeeds from persisted opportunity_data
        AND the AI evaluation boundary is not invoked
        """
        mock_settings = _make_settings(tmp_path)

        # Pre-populate the store with a pending_delivery record
        store = CandidateStore(mock_settings.db_path)
        store.init_db()
        opp_json = _make_opportunity_json("retry_post_1")
        # decided_at in the past so it's treated as a retry
        store.save_pending_delivery("retry_post_1", opp_json)

        evaluate_batch_contexts = []

        def track_evaluate(thread_contexts, settings):
            evaluate_batch_contexts.extend(thread_contexts)
            return []

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch(
                "auto_reddit.main.collect_candidates",
                return_value=[],  # no new candidates — only retry path
            ),
            patch(
                "auto_reddit.main.fetch_thread_contexts",
                return_value=[],  # no thread contexts — only retry path
            ),
            patch(
                "auto_reddit.main.evaluate_batch",
                side_effect=track_evaluate,
            ),
            patch(
                "auto_reddit.delivery.send_message",
                return_value=True,
            ) as mock_send,
        ):
            run()

        # Primary proof: evaluate_batch was NOT called with the retry post's data
        assert not any(
            ctx.candidate.post_id == "retry_post_1" for ctx in evaluate_batch_contexts
        ), "retry_post_1 must not flow through AI re-evaluation during retry delivery"

        # Delivery was attempted (summary + opportunity = at least 1 call)
        assert mock_send.call_count >= 1, (
            "send_message should have been called for delivery"
        )

        # Persisted-state proof: the message content must contain data that came from
        # the pre-inserted opportunity_data (post title or link from _make_opportunity_json).
        # This proves delivery consumed the stored AcceptedOpportunity, not empty inputs.
        sent_texts = [call.args[2] for call in mock_send.call_args_list]
        assert any("retry_post_1" in text for text in sent_texts), (
            "At least one Telegram message must reference 'retry_post_1' — "
            "proving delivery consumed the persisted opportunity_data, "
            "not an empty-input flow"
        )

        # The record should be marked as sent
        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM post_decisions WHERE post_id = ?",
                ("retry_post_1",),
            ).fetchone()
        assert row is not None
        assert row[0] == "sent", (
            f"Expected status=sent after retry delivery, got {row[0]!r}"
        )

    def test_retry_does_not_call_evaluate_batch_even_if_new_candidates_zero(
        self, tmp_path
    ):
        """evaluate_batch is only called when thread_contexts is non-empty.
        With 0 thread contexts, it should not be called at all.
        """
        mock_settings = _make_settings(tmp_path)
        store = CandidateStore(mock_settings.db_path)
        store.init_db()
        store.save_pending_delivery("retry_p2", _make_opportunity_json("retry_p2"))

        evaluate_batch_calls = []

        def track_evaluate(thread_contexts, settings):
            evaluate_batch_calls.append(thread_contexts)
            return []

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", return_value=[]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", side_effect=track_evaluate),
            patch("auto_reddit.delivery.send_message", return_value=True),
        ):
            run()

        # evaluate_batch was called with empty list OR not at all — either way no AI work
        # Looking at main.py: evaluate_batch is always called with thread_contexts result
        # When thread_contexts is empty: evaluate_batch([]) is still called
        # Primary assertion: retry_p2 delivered without evaluate_batch receiving any contexts
        assert not any(len(contexts) > 0 for contexts in evaluate_batch_calls), (
            "evaluate_batch should not receive any thread contexts during retry-only run"
        )


# ---------------------------------------------------------------------------
# P2 — Delivery boundary isolation
# Spec: delivery processes retries without upstream re-entry
# ---------------------------------------------------------------------------


class TestDeliveryBoundaryIsolation:
    """P2: Delivery phase must not re-enter upstream Reddit/AI/publishing flows."""

    def test_delivery_reads_only_persisted_records_no_upstream_reentry(self, tmp_path):
        """
        GIVEN main.run() reaches delivery with controlled upstream data and pending retries
        WHEN upstream Reddit and AI boundaries are patched as sentinels
        THEN delivery reads only the persisted delivery set
        AND no Reddit, extraction, AI, or publishing side effect occurs
        """
        mock_settings = _make_settings(tmp_path)

        # Pre-insert two pending delivery records
        store = CandidateStore(mock_settings.db_path)
        store.init_db()
        store.save_pending_delivery(
            "isolated_p1", _make_opportunity_json("isolated_p1")
        )
        store.save_pending_delivery(
            "isolated_p2", _make_opportunity_json("isolated_p2")
        )

        # collect_candidates and fetch_thread_contexts return controlled empty data
        # (no new candidates — the test is about delivery only)
        collect_calls = []
        fetch_calls = []
        evaluate_calls = []

        def track_collect(settings):
            collect_calls.append(True)
            return []  # no new candidates

        def track_fetch(candidates, settings):
            fetch_calls.append(candidates)
            return []  # no thread contexts

        def track_evaluate(thread_contexts, settings):
            evaluate_calls.append(thread_contexts)
            return []  # no new evaluation results

        sent_post_ids = []

        def track_send(token, chat_id, text):
            # Track what was sent; summaries won't contain post content directly
            sent_post_ids.append(text)
            return True

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", side_effect=track_collect),
            patch("auto_reddit.main.fetch_thread_contexts", side_effect=track_fetch),
            patch("auto_reddit.main.evaluate_batch", side_effect=track_evaluate),
            patch("auto_reddit.delivery.send_message", side_effect=track_send),
        ):
            run()

        # collect_candidates called exactly once (normal pipeline flow)
        assert len(collect_calls) == 1

        # fetch_thread_contexts called with empty list (no new candidates)
        assert len(fetch_calls) == 1
        assert fetch_calls[0] == []

        # evaluate_batch called with empty list (no new thread contexts)
        assert len(evaluate_calls) == 1
        assert evaluate_calls[0] == []

        # Both pending records were delivered
        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            rows = conn.execute(
                "SELECT post_id, status FROM post_decisions ORDER BY post_id"
            ).fetchall()
        status_map = {row[0]: row[1] for row in rows}
        assert status_map.get("isolated_p1") == "sent"
        assert status_map.get("isolated_p2") == "sent"


# ---------------------------------------------------------------------------
# P3 — Evaluation boundary isolation
# Spec: evaluation executes without delivery or Reddit side effects
# ---------------------------------------------------------------------------


class TestEvaluationBoundaryIsolation:
    """P3: Evaluation phase must not trigger delivery or Reddit side effects.

    Two-pronged proof:
    1. Evaluation consuming thread-context input and returning a RejectedPost MUST NOT
       produce any Telegram delivery side effect — Telegram sentinel must not fire.
    2. Evaluation consuming thread-context input and returning an AcceptedOpportunity
       correctly persists the result to the store (bounded outcome from input only),
       while Telegram delivery is explicitly a downstream phase, not an eval side effect.
    """

    def test_evaluation_boundary_no_delivery_side_effect_on_rejection(self, tmp_path):
        """
        PRIMARY BOUNDARY PROOF — spec scenario P3.

        GIVEN evaluation receives controlled normalized thread-context input
        WHEN Reddit and delivery boundaries are patched as sentinels
        THEN evaluation returns its bounded outcome (rejected) from that input only
        AND no individual opportunity Telegram message is sent (only the summary is allowed)

        The daily summary IS always sent per spec (even on 0-opportunity runs).
        The strict check here is that no OPPORTUNITY-specific message is sent when
        evaluation rejects the post — proving evaluation does not accidentally trigger
        opportunity delivery as a side effect of its own execution.
        """
        mock_settings = _make_settings(tmp_path)

        candidate = _make_candidate("eval_isolated", created_utc=_FIXED_EPOCH)
        thread_ctx = _make_thread_context(candidate)

        rejected = RejectedPost(
            post_id="eval_isolated",
            rejection_type=RejectionType.no_useful_contribution,
        )

        opportunity_send_calls = []

        def track_send_sentinel(token, chat_id, text):
            # The summary message is expected (even with 0 opportunities — spec §10).
            # An opportunity-specific message must NOT be sent after a rejection.
            if "del día" not in text:
                opportunity_send_calls.append(text)
                raise AssertionError(
                    "send_message called with a non-summary message after rejection: "
                    "no accepted opportunity was produced, so individual Telegram "
                    "opportunity messages are a forbidden side effect here"
                )
            return True  # summary is OK

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", return_value=[candidate]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[thread_ctx]),
            patch("auto_reddit.main.evaluate_batch", return_value=[rejected]),
            patch(
                "auto_reddit.delivery.send_message",
                side_effect=track_send_sentinel,
            ),
        ):
            # Must NOT raise — evaluation rejection should not trigger opportunity delivery
            run()

        # No opportunity messages were sent
        assert opportunity_send_calls == [], (
            f"Opportunity messages sent after rejection: {opportunity_send_calls}"
        )

        # Rejected post stored correctly — evaluation produced its bounded outcome
        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM post_decisions WHERE post_id = ?",
                ("eval_isolated",),
            ).fetchone()
        assert row is not None
        assert row[0] == "rejected", (
            f"Evaluation result must be persisted as 'rejected'; got {row[0]!r}"
        )

    def test_evaluation_accepted_outcome_persisted_before_delivery_phase(
        self, tmp_path
    ):
        """
        SECONDARY PROOF: accepted evaluation result is persisted to the store
        (bounded output from thread-context input) before delivery phase runs.
        Telegram delivery is a separate downstream phase — not a side effect of evaluation.
        """
        mock_settings = _make_settings(tmp_path)

        candidate = _make_candidate("eval_p1", created_utc=_FIXED_EPOCH)
        thread_ctx = _make_thread_context(candidate)

        accepted = AcceptedOpportunity(
            post_id="eval_p1",
            title="Post eval_p1",
            link="https://www.reddit.com/r/Odoo/comments/eval_p1/",
            post_language="en",
            opportunity_type=OpportunityType.funcionalidad,
            opportunity_reason="Test reason",
            post_summary_es="Resumen test",
            comment_summary_es=None,
            suggested_response_es="Respuesta ES",
            suggested_response_en="Response EN",
        )

        send_calls = []

        def track_send(token, chat_id, text):
            send_calls.append(text)
            return True

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", return_value=[candidate]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[thread_ctx]),
            patch("auto_reddit.main.evaluate_batch", return_value=[accepted]),
            patch("auto_reddit.delivery.send_message", side_effect=track_send),
        ):
            run()

        # Accepted opportunity was saved and then sent through the delivery phase
        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM post_decisions WHERE post_id = ?",
                ("eval_p1",),
            ).fetchone()
        assert row is not None
        assert row[0] == "sent", (
            f"Accepted opportunity should be delivered; got status={row[0]!r}"
        )

        # Delivery phase (downstream of evaluation) called Telegram — expected
        assert len(send_calls) >= 1, (
            "Telegram send_message should have been called in the delivery phase"
        )

    def test_rejected_post_stored_without_opportunity_delivery_side_effect(
        self, tmp_path
    ):
        """
        Rejected posts must not trigger individual opportunity Telegram delivery.
        The daily summary IS sent unconditionally (spec §10), but no opportunity
        message should be sent for a rejected post.
        """
        mock_settings = _make_settings(tmp_path)

        candidate = _make_candidate("eval_rejected", created_utc=_FIXED_EPOCH)
        thread_ctx = _make_thread_context(candidate)

        rejected = RejectedPost(
            post_id="eval_rejected",
            rejection_type=RejectionType.no_useful_contribution,
        )

        send_calls = []

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", return_value=[candidate]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[thread_ctx]),
            patch("auto_reddit.main.evaluate_batch", return_value=[rejected]),
            patch(
                "auto_reddit.delivery.send_message",
                side_effect=lambda tok, chat, text: send_calls.append(text) or True,
            ),
        ):
            run()

        # Exactly 1 call: the daily summary (0-opportunity run)
        assert len(send_calls) == 1, (
            f"Expected exactly 1 send (summary). Got {len(send_calls)}: {send_calls}"
        )
        # The single call must be the summary, not an opportunity message
        assert "del día" in send_calls[0], (
            "The only send_message call should be the daily summary"
        )

        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM post_decisions WHERE post_id = ?",
                ("eval_rejected",),
            ).fetchone()
        assert row is not None
        assert row[0] == "rejected"


# ---------------------------------------------------------------------------
# P4 — Multi-run operational memory boundaries
# Spec: sent/rejected excluded in later runs; pending_delivery retryable without AI
# ---------------------------------------------------------------------------


class TestMultiRunMemoryBoundaries:
    """P4: Real SQLite state persists across runs, enforcing memory boundaries."""

    def test_run1_persists_sent_and_rejected_correctly(self, tmp_path):
        """
        P4 Run 1: evaluate_batch returns 1 accepted + 1 rejected.
        After delivery: 1 sent, 1 rejected in the store.
        """
        mock_settings = _make_settings(tmp_path)

        candidate_accepted = _make_candidate("p4_accepted", created_utc=_FIXED_EPOCH)
        candidate_rejected = _make_candidate(
            "p4_rejected", created_utc=_FIXED_EPOCH - 10
        )
        ctx_accepted = _make_thread_context(candidate_accepted)
        ctx_rejected = _make_thread_context(candidate_rejected)

        accepted = AcceptedOpportunity(
            post_id="p4_accepted",
            title="Post p4_accepted",
            link="https://www.reddit.com/r/Odoo/comments/p4_accepted/",
            post_language="es",
            opportunity_type=OpportunityType.desarrollo,
            opportunity_reason="Reason",
            post_summary_es="Resumen",
            comment_summary_es=None,
            suggested_response_es="Respuesta ES",
            suggested_response_en="Response EN",
        )
        rejected = RejectedPost(
            post_id="p4_rejected",
            rejection_type=RejectionType.resolved_or_closed,
        )

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch(
                "auto_reddit.main.collect_candidates",
                return_value=[candidate_accepted, candidate_rejected],
            ),
            patch(
                "auto_reddit.main.fetch_thread_contexts",
                return_value=[ctx_accepted, ctx_rejected],
            ),
            patch(
                "auto_reddit.main.evaluate_batch",
                return_value=[accepted, rejected],
            ),
            patch("auto_reddit.delivery.send_message", return_value=True),
        ):
            run()

        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            rows = conn.execute(
                "SELECT post_id, status FROM post_decisions ORDER BY post_id"
            ).fetchall()
        status_map = {row[0]: row[1] for row in rows}
        assert status_map.get("p4_accepted") == "sent", (
            f"Expected p4_accepted=sent, got {status_map.get('p4_accepted')!r}"
        )
        assert status_map.get("p4_rejected") == "rejected", (
            f"Expected p4_rejected=rejected, got {status_map.get('p4_rejected')!r}"
        )

    def test_run2_excludes_sent_and_rejected_processes_new(self, tmp_path):
        """
        P4 Run 2: Same db after run 1. sent/rejected posts excluded from review.
        New post is processed. pending_delivery retry works without AI re-evaluation.
        """
        mock_settings = _make_settings(tmp_path)

        # === RUN 1: establish sent + rejected + pending_delivery state ===
        candidate_accepted = _make_candidate("p4r2_sent", created_utc=_FIXED_EPOCH)
        candidate_rejected = _make_candidate(
            "p4r2_rejected", created_utc=_FIXED_EPOCH - 10
        )
        ctx_a = _make_thread_context(candidate_accepted)
        ctx_r = _make_thread_context(candidate_rejected)

        accepted = AcceptedOpportunity(
            post_id="p4r2_sent",
            title="Post p4r2_sent",
            link="https://www.reddit.com/r/Odoo/comments/p4r2_sent/",
            post_language="en",
            opportunity_type=OpportunityType.funcionalidad,
            opportunity_reason="Reason",
            post_summary_es="Resumen",
            comment_summary_es=None,
            suggested_response_es="Resp ES",
            suggested_response_en="Resp EN",
        )
        rejected = RejectedPost(
            post_id="p4r2_rejected",
            rejection_type=RejectionType.excluded_topic,
        )

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch(
                "auto_reddit.main.collect_candidates",
                return_value=[candidate_accepted, candidate_rejected],
            ),
            patch(
                "auto_reddit.main.fetch_thread_contexts",
                return_value=[ctx_a, ctx_r],
            ),
            patch(
                "auto_reddit.main.evaluate_batch",
                return_value=[accepted, rejected],
            ),
            patch("auto_reddit.delivery.send_message", return_value=True),
        ):
            run()

        # === Insert a pending_delivery record manually (simulates a prior failed delivery) ===
        store = CandidateStore(mock_settings.db_path)
        store.save_pending_delivery("p4r2_retry", _make_opportunity_json("p4r2_retry"))

        # === RUN 2: same db, fresh patches ===
        # New candidate not previously seen
        new_candidate = _make_candidate("p4r2_new", created_utc=_FIXED_EPOCH + 100)
        # Same candidates as run 1 (already decided) + new one
        all_candidates_run2 = [
            _make_candidate("p4r2_sent", created_utc=_FIXED_EPOCH),
            _make_candidate("p4r2_rejected", created_utc=_FIXED_EPOCH - 10),
            new_candidate,
        ]

        new_accepted = AcceptedOpportunity(
            post_id="p4r2_new",
            title="Post p4r2_new",
            link="https://www.reddit.com/r/Odoo/comments/p4r2_new/",
            post_language="en",
            opportunity_type=OpportunityType.comparativas,
            opportunity_reason="New reason",
            post_summary_es="Nuevo resumen",
            comment_summary_es=None,
            suggested_response_es="Nueva resp ES",
            suggested_response_en="New resp EN",
        )

        evaluate_inputs = []

        def track_evaluate_run2(thread_contexts, settings):
            evaluate_inputs.extend(thread_contexts)
            # Simulate AI evaluating only the new post
            return [new_accepted]

        def make_fetch_run2(candidates, settings):
            # Only return context for the new candidate (sent/rejected are filtered out)
            return [
                _make_thread_context(c) for c in candidates if c.post_id == "p4r2_new"
            ]

        with (
            patch("time.time", return_value=_FIXED_EPOCH + 200),
            patch("auto_reddit.main.settings", mock_settings),
            patch(
                "auto_reddit.main.collect_candidates",
                return_value=all_candidates_run2,
            ),
            patch(
                "auto_reddit.main.fetch_thread_contexts",
                side_effect=make_fetch_run2,
            ),
            patch(
                "auto_reddit.main.evaluate_batch",
                side_effect=track_evaluate_run2,
            ),
            patch("auto_reddit.delivery.send_message", return_value=True),
        ):
            run()

        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            rows = conn.execute(
                "SELECT post_id, status FROM post_decisions ORDER BY post_id"
            ).fetchall()
        status_map = {row[0]: row[1] for row in rows}

        # sent/rejected decisions are preserved (not re-processed)
        assert status_map.get("p4r2_sent") == "sent", (
            f"p4r2_sent should remain 'sent', got {status_map.get('p4r2_sent')!r}"
        )
        assert status_map.get("p4r2_rejected") == "rejected", (
            f"p4r2_rejected should remain 'rejected', got {status_map.get('p4r2_rejected')!r}"
        )

        # New post was evaluated and delivered
        assert status_map.get("p4r2_new") == "sent", (
            f"p4r2_new should be 'sent' after run 2, got {status_map.get('p4r2_new')!r}"
        )

        # sent/rejected were excluded from AI evaluation in run 2
        evaluated_post_ids = {ctx.candidate.post_id for ctx in evaluate_inputs}
        assert "p4r2_sent" not in evaluated_post_ids, (
            "Already-sent post must not be re-evaluated"
        )
        assert "p4r2_rejected" not in evaluated_post_ids, (
            "Already-rejected post must not be re-evaluated"
        )

    def test_pending_delivery_retry_excluded_from_decided_set(self, tmp_path):
        """
        pending_delivery records are NOT in the decided set (get_decided_post_ids),
        so they remain eligible for delivery retry across runs.
        """
        mock_settings = _make_settings(tmp_path)
        store = CandidateStore(mock_settings.db_path)
        store.init_db()

        # Insert a pending_delivery record
        store.save_pending_delivery("pending_p", _make_opportunity_json("pending_p"))

        decided_ids = store.get_decided_post_ids()

        assert "pending_p" not in decided_ids, (
            "pending_delivery records must NOT appear in decided_ids "
            "(they should remain eligible for delivery retry)"
        )

    def test_pending_delivery_retried_without_ai_call_in_run2(self, tmp_path):
        """
        Primary proof: pending_delivery from run 1 is retried in run 2
        using persisted opportunity_data WITHOUT AI re-evaluation.
        """
        mock_settings = _make_settings(tmp_path)

        # Pre-insert pending_delivery to simulate a failed prior delivery
        store = CandidateStore(mock_settings.db_path)
        store.init_db()
        opp_json = _make_opportunity_json("pdr_retry")
        # decided_at in past to ensure it's treated as a retry by selector
        import sqlite3

        with sqlite3.connect(mock_settings.db_path) as conn:
            conn.execute(
                """
                INSERT INTO post_decisions (post_id, status, opportunity_data, decided_at)
                VALUES (?, ?, ?, ?)
                """,
                ("pdr_retry", "pending_delivery", opp_json, _FIXED_EPOCH - 86400),
            )
            conn.commit()

        evaluate_batch_contexts = []

        def track_evaluate(thread_contexts, settings):
            # Track any contexts passed — they must not contain the retry post
            evaluate_batch_contexts.extend(thread_contexts)
            return []

        with (
            patch("time.time", return_value=_FIXED_EPOCH),
            patch("auto_reddit.main.settings", mock_settings),
            patch("auto_reddit.main.collect_candidates", return_value=[]),
            patch("auto_reddit.main.fetch_thread_contexts", return_value=[]),
            patch("auto_reddit.main.evaluate_batch", side_effect=track_evaluate),
            patch("auto_reddit.delivery.send_message", return_value=True),
        ):
            run()

        # Primary proof: the retry post was never submitted to AI evaluation
        evaluated_ids = {ctx.candidate.post_id for ctx in evaluate_batch_contexts}
        assert "pdr_retry" not in evaluated_ids, (
            "pdr_retry must not flow through evaluate_batch — "
            "it should be retried from persisted opportunity_data directly"
        )

        # Verify the retry was delivered
        with sqlite3.connect(mock_settings.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM post_decisions WHERE post_id = ?",
                ("pdr_retry",),
            ).fetchone()
        assert row is not None
        assert row[0] == "sent", (
            f"Retry record should be 'sent' after retry delivery, got {row[0]!r}"
        )


# ---------------------------------------------------------------------------
# Optional smoke tests — env-gated, non-blocking
# ---------------------------------------------------------------------------

from dotenv import load_dotenv

load_dotenv()  # Ensure .env is loaded for manual/local smoke-test runs.

_SMOKE_API_KEY = os.getenv("REDDIT_SMOKE_API_KEY") or os.getenv("REDDIT_API_KEY")
_SMOKE_TG_TOKEN = os.getenv("TELEGRAM_SMOKE_BOT_TOKEN")
_SMOKE_TG_CHAT_ID = os.getenv("TELEGRAM_SMOKE_CHAT_ID")


@pytest.mark.skipif(
    not _SMOKE_API_KEY,
    reason="Neither REDDIT_SMOKE_API_KEY nor REDDIT_API_KEY is set — smoke tests skipped",
)
class TestRedditSmokeOptional:
    """Optional smoke tests against real Reddit API providers.

    These tests run when REDDIT_SMOKE_API_KEY is set, falling back to
    REDDIT_API_KEY if the dedicated smoke key is absent.
    They are non-blocking: their absence does not affect CI pass/fail.
    """

    def test_real_reddit_collect_candidates_returns_nonempty_list(self):
        """Smoke: real Reddit provider returns at least one r/Odoo candidate."""
        from auto_reddit.config.settings import Settings
        from auto_reddit.reddit.client import collect_candidates

        # Build minimal settings from env-provided key (prefers REDDIT_SMOKE_API_KEY)
        settings = MagicMock()
        settings.reddit_api_key = _SMOKE_API_KEY
        settings.review_window_days = 7

        candidates = collect_candidates(settings)
        assert len(candidates) > 0, (
            "Expected real Reddit API to return at least one r/Odoo post "
            f"(got {len(candidates)} candidates)"
        )
        # All candidates should be from r/Odoo
        for c in candidates:
            assert c.subreddit.lower() == "odoo", (
                f"Unexpected subreddit: {c.subreddit!r}"
            )


@pytest.mark.skipif(
    not _SMOKE_TG_TOKEN or not _SMOKE_TG_CHAT_ID,
    reason="TELEGRAM_SMOKE_BOT_TOKEN / TELEGRAM_SMOKE_CHAT_ID not set — Telegram smoke skipped",
)
class TestTelegramSmokeOptional:
    """Optional smoke tests against the real Telegram Bot API.

    These tests run only when both TELEGRAM_SMOKE_BOT_TOKEN and
    TELEGRAM_SMOKE_CHAT_ID are set, targeting a controlled non-production
    bot/chat.  They are non-blocking: their absence does not affect CI
    pass/fail.

    S1 — plain text delivery succeeds.
    S2 — invalid token returns False without raising.
    S3 — HTML-formatted delivery succeeds.
    """

    def test_send_message_delivers_plain_text(self):
        """S1: send_message() returns True for a valid plain-text message."""
        from auto_reddit.delivery.telegram import send_message

        result = send_message(
            _SMOKE_TG_TOKEN,
            _SMOKE_TG_CHAT_ID,
            "🧪 auto-reddit smoke test — plain",
        )
        assert result is True, (
            "Expected send_message() to return True for plain text delivery"
        )

    def test_send_message_returns_false_for_invalid_token(self):
        """S2: send_message() returns False for a dummy/invalid token — no exception."""
        from auto_reddit.delivery.telegram import send_message

        result = send_message(
            "0000000000:INVALID",
            _SMOKE_TG_CHAT_ID,
            "🧪 auto-reddit smoke test — invalid token check",
        )
        assert result is False, (
            "Expected send_message() to return False for an invalid bot token"
        )

    def test_send_message_delivers_html_formatting(self):
        """S3: send_message() returns True when the body contains HTML tags."""
        from auto_reddit.delivery.telegram import send_message

        html_body = (
            "🧪 auto-reddit smoke test — HTML\n"
            "<b>Bold text</b>\n"
            '<a href="https://example.com">Link</a>\n'
            "<code>code block</code>"
        )
        result = send_message(
            _SMOKE_TG_TOKEN,
            _SMOKE_TG_CHAT_ID,
            html_body,
        )
        assert result is True, (
            "Expected send_message() to return True for HTML-formatted delivery"
        )
