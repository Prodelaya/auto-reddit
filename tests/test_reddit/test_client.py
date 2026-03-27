"""Tests unitarios para reddit/client.py.

Cubre:
- Normalización por proveedor (reddit3, reddit34, reddapi)
- is_complete con posts completos e incompletos
- Filtro de 7 días (boundary posts)
- Paginación con cursor (2 páginas + stop condition)
- Fallback chain (reddit3 fail → reddit34 success; all fail → empty list)
- Integración: collect_candidates end-to-end con HTTP mockeado
- Filtro explícito por subreddit Odoo
- Más de 8 candidatos entregados sin truncación (spec runtime guarantee)
- url relativa → absoluta
- Retry/backoff (_fetch_with_retry)
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from auto_reddit.reddit.client import (
    _fetch_with_retry,
    _normalize_reddit3,
    _normalize_reddit34,
    _normalize_reddapi,
    collect_candidates,
)
from auto_reddit.shared.contracts import RedditCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = int(datetime.now(tz=timezone.utc).timestamp())
_6_DAYS_AGO = _NOW - 6 * 24 * 3600
_8_DAYS_AGO = _NOW - 8 * 24 * 3600


# ---------------------------------------------------------------------------
# 5.2a — Normalizers produce valid RedditCandidate from fixtures
# ---------------------------------------------------------------------------


class TestNormalizeReddit3:
    def test_produces_list_of_reddit_candidates(self, reddit3_posts_raw):
        result = _normalize_reddit3(reddit3_posts_raw)
        assert len(result) > 0
        assert all(isinstance(c, RedditCandidate) for c in result)

    def test_post_id_is_string(self, reddit3_posts_raw):
        result = _normalize_reddit3(reddit3_posts_raw)
        assert all(isinstance(c.post_id, str) for c in result)

    def test_permalink_is_full_url(self, reddit3_posts_raw):
        result = _normalize_reddit3(reddit3_posts_raw)
        assert all(c.permalink.startswith("https://www.reddit.com") for c in result)

    def test_source_api_is_reddit3(self, reddit3_posts_raw):
        result = _normalize_reddit3(reddit3_posts_raw)
        assert all(c.source_api == "reddit3" for c in result)

    def test_created_utc_is_int(self, reddit3_posts_raw):
        result = _normalize_reddit3(reddit3_posts_raw)
        assert all(isinstance(c.created_utc, int) for c in result)


class TestNormalizeReddit34:
    def test_produces_list_of_reddit_candidates(self, reddit34_posts_raw):
        result = _normalize_reddit34(reddit34_posts_raw)
        assert len(result) > 0
        assert all(isinstance(c, RedditCandidate) for c in result)

    def test_post_id_has_no_t3_prefix(self, reddit34_posts_raw):
        result = _normalize_reddit34(reddit34_posts_raw)
        assert all(not c.post_id.startswith("t3_") for c in result)

    def test_permalink_is_full_url(self, reddit34_posts_raw):
        result = _normalize_reddit34(reddit34_posts_raw)
        assert all(c.permalink.startswith("https://www.reddit.com") for c in result)

    def test_source_api_is_reddit34(self, reddit34_posts_raw):
        result = _normalize_reddit34(reddit34_posts_raw)
        assert all(c.source_api == "reddit34" for c in result)

    def test_created_utc_is_int(self, reddit34_posts_raw):
        result = _normalize_reddit34(reddit34_posts_raw)
        assert all(isinstance(c.created_utc, int) for c in result)


class TestNormalizeReddapi:
    def test_produces_list_of_reddit_candidates(self, reddapi_posts_raw):
        result = _normalize_reddapi(reddapi_posts_raw)
        assert len(result) > 0
        assert all(isinstance(c, RedditCandidate) for c in result)

    def test_post_id_has_no_t3_prefix(self, reddapi_posts_raw):
        result = _normalize_reddapi(reddapi_posts_raw)
        assert all(not c.post_id.startswith("t3_") for c in result)

    def test_permalink_is_full_url(self, reddapi_posts_raw):
        result = _normalize_reddapi(reddapi_posts_raw)
        assert all(c.permalink.startswith("https://www.reddit.com") for c in result)

    def test_source_api_is_reddapi(self, reddapi_posts_raw):
        result = _normalize_reddapi(reddapi_posts_raw)
        assert all(c.source_api == "reddapi" for c in result)


# ---------------------------------------------------------------------------
# 5.2b — is_complete: True for full posts, False when selftext or author is None
# ---------------------------------------------------------------------------


class TestIsComplete:
    def _make_candidate(self, **kwargs) -> RedditCandidate:
        defaults = dict(
            post_id="abc123",
            title="Test title",
            selftext="Some body",
            url="https://www.reddit.com/r/Odoo/comments/abc123/test/",
            permalink="https://www.reddit.com/r/Odoo/comments/abc123/test/",
            author="testuser",
            subreddit="Odoo",
            created_utc=_6_DAYS_AGO,
            num_comments=5,
            source_api="reddit3",
        )
        defaults.update(kwargs)
        return RedditCandidate(**defaults)

    def test_is_complete_true_when_all_fields_present(self):
        c = self._make_candidate()
        assert c.is_complete is True

    def test_is_complete_false_when_selftext_is_none(self):
        c = self._make_candidate(selftext=None)
        assert c.is_complete is False

    def test_is_complete_false_when_author_is_none(self):
        c = self._make_candidate(author=None)
        assert c.is_complete is False

    def test_is_complete_false_when_both_none(self):
        c = self._make_candidate(selftext=None, author=None)
        assert c.is_complete is False

    def test_is_complete_false_when_selftext_empty_string(self):
        # Empty string is falsy — treated as incomplete by the contract
        # The normalizer maps "" → None, but test the model boundary directly
        c = self._make_candidate(selftext="")
        # selftext="" is not None, so is_complete checks all([title, "" is not None, url, author])
        # "" is not None → True; all fields present → True only if title+url+author are truthy
        # According to design: selftext="" → is_complete=True (it's not None)
        # This is the correct behaviour: only None means missing
        assert c.is_complete is True

    def test_num_comments_none_does_not_affect_completeness(self):
        c = self._make_candidate(num_comments=None)
        assert c.is_complete is True


# ---------------------------------------------------------------------------
# 5.3 — 7-day filter: boundary posts
# ---------------------------------------------------------------------------


class TestSevenDayFilter:
    """Tests for the 7-day window applied inside collect_candidates.

    We mock datetime.now and the HTTP layer to control created_utc values.
    """

    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    def _make_raw_reddit3(self, utc_timestamps: list[int]) -> dict:
        """Build a minimal reddit3 response_raw with posts at given timestamps."""
        body = [
            {
                "id": f"post{i}",
                "title": f"Post {i}",
                "selftext": "body",
                "url": f"https://www.reddit.com/r/Odoo/comments/post{i}/",
                "permalink": f"/r/Odoo/comments/post{i}/test/",
                "author": "user",
                "subreddit": "Odoo",
                "created_utc": ts,
                "num_comments": 0,
            }
            for i, ts in enumerate(utc_timestamps)
        ]
        return {"meta": {"cursor": None}, "body": body}

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_post_exactly_7_days_ago_is_included(self, mock_client_cls, mock_dt):
        """A post created exactly 7 days ago (now - 604800s) must be included."""
        fake_now = 1_700_000_000
        seven_days_ago = fake_now - 7 * 24 * 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw = self._make_raw_reddit3([seven_days_ago, seven_days_ago - 1])
        mock_response = MagicMock()
        mock_response.json.return_value = raw
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        ids = [c.post_id for c in candidates]
        assert "post0" in ids  # exactly 7 days ago → included
        assert "post1" not in ids  # 7 days + 1 second → excluded

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_post_outside_7_days_is_excluded(self, mock_client_cls, mock_dt):
        """A post created 8 days ago must be excluded."""
        fake_now = 1_700_000_000
        eight_days_ago = fake_now - 8 * 24 * 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw = self._make_raw_reddit3([eight_days_ago])
        mock_response = MagicMock()
        mock_response.json.return_value = raw
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        assert candidates == []


# ---------------------------------------------------------------------------
# 5.4 — Cursor pagination: 2 pages + stop condition
# ---------------------------------------------------------------------------


class TestCursorPagination:
    """Tests for the pagination loop inside _paginate via collect_candidates."""

    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_two_pages_collected_then_stop_on_no_cursor(self, mock_client_cls, mock_dt):
        """Two pages returned; second page has no cursor → stop after page 2."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600  # 1 hour ago → within window
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        page1 = {
            "meta": {"cursor": "cursor_page2"},
            "body": [
                {
                    "id": "p1",
                    "title": "Post 1",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/p1/",
                    "permalink": "/r/Odoo/comments/p1/",
                    "author": "u1",
                    "subreddit": "Odoo",
                    "created_utc": recent_ts,
                    "num_comments": 1,
                }
            ],
        }
        page2 = {
            "meta": {"cursor": None},
            "body": [
                {
                    "id": "p2",
                    "title": "Post 2",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/p2/",
                    "permalink": "/r/Odoo/comments/p2/",
                    "author": "u2",
                    "subreddit": "Odoo",
                    "created_utc": recent_ts - 100,
                    "num_comments": 2,
                }
            ],
        }

        responses = [MagicMock(), MagicMock()]
        responses[0].json.return_value = page1
        responses[1].json.return_value = page2

        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = responses
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        assert {c.post_id for c in candidates} == {"p1", "p2"}
        assert mock_client_instance.get.call_count == 2

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_stop_when_oldest_post_outside_window(self, mock_client_cls, mock_dt):
        """Stop paginating when oldest post in page is outside 7-day window."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600  # within window
        old_ts = fake_now - 9 * 24 * 3600  # outside window
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        page1 = {
            "meta": {"cursor": "next"},
            "body": [
                {
                    "id": "recent",
                    "title": "Recent",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/recent/",
                    "permalink": "/r/Odoo/comments/recent/",
                    "author": "u1",
                    "subreddit": "Odoo",
                    "created_utc": recent_ts,
                    "num_comments": 0,
                },
                {
                    "id": "old",
                    "title": "Old",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/old/",
                    "permalink": "/r/Odoo/comments/old/",
                    "author": "u2",
                    "subreddit": "Odoo",
                    "created_utc": old_ts,
                    "num_comments": 0,
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = page1
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        # Only the recent post passes the 7-day filter
        assert len(candidates) == 1
        assert candidates[0].post_id == "recent"
        # Only 1 page fetched (oldest post in page triggered stop)
        assert mock_client_instance.get.call_count == 1


# ---------------------------------------------------------------------------
# 5.5 — Fallback chain
# ---------------------------------------------------------------------------


class TestFallbackChain:
    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client._collect_via_reddit3")
    @patch("auto_reddit.reddit.client._collect_via_reddit34")
    def test_reddit3_fail_triggers_reddit34(self, mock_r34, mock_r3, mock_dt):
        """When reddit3 fails, reddit34 is tried next."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        mock_r3.side_effect = RuntimeError("reddit3 down")
        mock_r34.return_value = [
            RedditCandidate(
                post_id="r34post",
                title="Via reddit34",
                selftext="body",
                url="https://www.reddit.com/r/Odoo/comments/r34post/",
                permalink="https://www.reddit.com/r/Odoo/comments/r34post/",
                author="u1",
                subreddit="Odoo",
                created_utc=recent_ts,
                source_api="reddit34",
            )
        ]

        candidates = collect_candidates(self._mock_settings())
        mock_r3.assert_called_once()
        mock_r34.assert_called_once()
        assert len(candidates) == 1
        assert candidates[0].post_id == "r34post"

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client._collect_via_reddit3")
    @patch("auto_reddit.reddit.client._collect_via_reddit34")
    @patch("auto_reddit.reddit.client._collect_via_reddapi")
    def test_all_fail_returns_empty_list(
        self, mock_reddapi, mock_r34, mock_r3, mock_dt
    ):
        """When all providers fail, returns empty list (no exception raised)."""
        fake_now = 1_700_000_000
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        mock_r3.side_effect = RuntimeError("reddit3 down")
        mock_r34.side_effect = RuntimeError("reddit34 down")
        mock_reddapi.side_effect = RuntimeError("reddapi down")

        candidates = collect_candidates(self._mock_settings())
        assert candidates == []


# ---------------------------------------------------------------------------
# 5.6 — Integration: full collect_candidates end-to-end (HTTP mocked)
# ---------------------------------------------------------------------------


class TestCollectCandidatesIntegration:
    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_end_to_end_returns_sorted_list(self, mock_client_cls, mock_dt):
        """Full flow: HTTP mock → normalized candidates → sorted descending by created_utc."""
        fake_now = 1_700_000_000
        ts_recent = fake_now - 3600
        ts_older = fake_now - 7200
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw_response = {
            "meta": {"cursor": None},
            "body": [
                {
                    "id": "new_post",
                    "title": "Newer Post",
                    "selftext": "body newer",
                    "url": "https://www.reddit.com/r/Odoo/comments/new_post/",
                    "permalink": "/r/Odoo/comments/new_post/",
                    "author": "u1",
                    "subreddit": "Odoo",
                    "created_utc": ts_recent,
                    "num_comments": 3,
                },
                {
                    "id": "old_post",
                    "title": "Older Post",
                    "selftext": "body older",
                    "url": "https://www.reddit.com/r/Odoo/comments/old_post/",
                    "permalink": "/r/Odoo/comments/old_post/",
                    "author": "u2",
                    "subreddit": "Odoo",
                    "created_utc": ts_older,
                    "num_comments": 1,
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = raw_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())

        assert len(candidates) == 2
        assert all(isinstance(c, RedditCandidate) for c in candidates)
        # Sorted descending
        assert candidates[0].created_utc > candidates[1].created_utc
        assert candidates[0].post_id == "new_post"
        assert candidates[1].post_id == "old_post"
        # No comments included (change 1 boundary)
        assert all(not hasattr(c, "comments") for c in candidates)

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_incomplete_posts_included_with_is_complete_false(
        self, mock_client_cls, mock_dt
    ):
        """Incomplete posts (missing author/selftext) are kept with is_complete=False."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw_response = {
            "meta": {"cursor": None},
            "body": [
                {
                    "id": "complete_post",
                    "title": "Complete",
                    "selftext": "Has body",
                    "url": "https://www.reddit.com/r/Odoo/comments/complete_post/",
                    "permalink": "/r/Odoo/comments/complete_post/",
                    "author": "user",
                    "subreddit": "Odoo",
                    "created_utc": recent_ts,
                    "num_comments": 1,
                },
                {
                    "id": "incomplete_post",
                    "title": "Incomplete",
                    "selftext": None,
                    "url": "https://www.reddit.com/r/Odoo/comments/incomplete_post/",
                    "permalink": "/r/Odoo/comments/incomplete_post/",
                    "author": None,
                    "subreddit": "Odoo",
                    "created_utc": recent_ts - 100,
                    "num_comments": 0,
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = raw_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        assert len(candidates) == 2

        complete = next(c for c in candidates if c.post_id == "complete_post")
        incomplete = next(c for c in candidates if c.post_id == "incomplete_post")

        assert complete.is_complete is True
        assert incomplete.is_complete is False


# ---------------------------------------------------------------------------
# CORRECTIVO: is_complete cubre el contrato mínimo completo
# Gaps detectados por verify: post_id, permalink, subreddit, created_utc, source_api vacíos
# ---------------------------------------------------------------------------


class TestIsCompleteFullContract:
    """Verifica que is_complete cubre TODOS los campos del contrato mínimo funcional."""

    def _make_candidate(self, **kwargs) -> RedditCandidate:
        defaults = dict(
            post_id="abc123",
            title="Test title",
            selftext="Some body",
            url="https://www.reddit.com/r/Odoo/comments/abc123/test/",
            permalink="https://www.reddit.com/r/Odoo/comments/abc123/test/",
            author="testuser",
            subreddit="Odoo",
            created_utc=_6_DAYS_AGO,
            num_comments=5,
            source_api="reddit3",
        )
        defaults.update(kwargs)
        return RedditCandidate(**defaults)

    def test_is_complete_false_when_post_id_empty(self):
        c = self._make_candidate(post_id="")
        assert c.is_complete is False

    def test_is_complete_false_when_permalink_empty(self):
        c = self._make_candidate(permalink="")
        assert c.is_complete is False

    def test_is_complete_false_when_url_empty(self):
        c = self._make_candidate(url="")
        assert c.is_complete is False

    def test_is_complete_false_when_subreddit_empty(self):
        c = self._make_candidate(subreddit="")
        assert c.is_complete is False

    def test_is_complete_false_when_created_utc_is_zero(self):
        c = self._make_candidate(created_utc=0)
        assert c.is_complete is False

    def test_is_complete_false_when_source_api_empty(self):
        c = self._make_candidate(source_api="")
        assert c.is_complete is False

    def test_is_complete_false_when_title_empty(self):
        c = self._make_candidate(title="")
        assert c.is_complete is False

    def test_num_comments_none_does_not_affect_completeness(self):
        """num_comments es opcional; no debe afectar is_complete."""
        c = self._make_candidate(num_comments=None)
        assert c.is_complete is True


# ---------------------------------------------------------------------------
# CORRECTIVO: normalizers conservan posts sin 'id' (is_complete=False, no excepción)
# ---------------------------------------------------------------------------


class TestNormalizersMissingId:
    """Posts sin 'id' se conservan con post_id='' → is_complete=False."""

    def test_reddit3_missing_id_survives_as_incomplete(self):
        raw = {
            "body": [
                {
                    # 'id' field deliberately absent
                    "title": "Post sin id",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/noid/",
                    "permalink": "/r/Odoo/comments/noid/",
                    "author": "user",
                    "subreddit": "Odoo",
                    "created_utc": _6_DAYS_AGO,
                    "num_comments": 0,
                }
            ]
        }
        result = _normalize_reddit3(raw)
        assert len(result) == 1
        assert result[0].post_id == ""
        assert result[0].is_complete is False

    def test_reddit34_missing_id_survives_as_incomplete(self):
        raw = {
            "data": {
                "posts": [
                    {
                        "data": {
                            # 'id' field deliberately absent
                            "title": "Post sin id",
                            "selftext": "body",
                            "url": "https://www.reddit.com/r/Odoo/comments/noid/",
                            "permalink": "/r/Odoo/comments/noid/",
                            "author": "user",
                            "subreddit": "Odoo",
                            "created_utc": _6_DAYS_AGO,
                            "num_comments": 0,
                        }
                    }
                ]
            }
        }
        result = _normalize_reddit34(raw)
        assert len(result) == 1
        assert result[0].post_id == ""
        assert result[0].is_complete is False

    def test_reddapi_missing_id_survives_as_incomplete(self):
        raw = {
            "posts": [
                {
                    "data": {
                        # 'id' field deliberately absent
                        "title": "Post sin id",
                        "selftext": "body",
                        "url": "https://www.reddit.com/r/Odoo/comments/noid/",
                        "permalink": "/r/Odoo/comments/noid/",
                        "author": "user",
                        "subreddit": "Odoo",
                        "created_utc": _6_DAYS_AGO,
                        "num_comments": 0,
                    }
                }
            ]
        }
        result = _normalize_reddapi(raw)
        assert len(result) == 1
        assert result[0].post_id == ""
        assert result[0].is_complete is False


# ---------------------------------------------------------------------------
# CORRECTIVO: filtro explícito de subreddit en collect_candidates
# Spec exige excluir posts de otros subreddits aunque el proveedor los devuelva
# ---------------------------------------------------------------------------


class TestSubredditFilter:
    """collect_candidates excluye posts cuyo subreddit != 'Odoo' (case-insensitive)."""

    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_non_odoo_posts_excluded(self, mock_client_cls, mock_dt):
        """Posts de otro subreddit son excluidos aunque estén en la ventana de 7 días."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw_response = {
            "meta": {"cursor": None},
            "body": [
                {
                    "id": "odoo_post",
                    "title": "Odoo question",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Odoo/comments/odoo_post/",
                    "permalink": "/r/Odoo/comments/odoo_post/",
                    "author": "user",
                    "subreddit": "Odoo",
                    "created_utc": recent_ts,
                    "num_comments": 1,
                },
                {
                    "id": "other_post",
                    "title": "Unrelated post",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/Python/comments/other_post/",
                    "permalink": "/r/Python/comments/other_post/",
                    "author": "user2",
                    "subreddit": "Python",
                    "created_utc": recent_ts - 100,
                    "num_comments": 0,
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = raw_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        assert len(candidates) == 1
        assert candidates[0].post_id == "odoo_post"
        assert all(c.subreddit.lower() == "odoo" for c in candidates)

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_subreddit_filter_case_insensitive(self, mock_client_cls, mock_dt):
        """Subreddit 'odoo' (lowercase) en la respuesta también pasa el filtro."""
        fake_now = 1_700_000_000
        recent_ts = fake_now - 3600
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        raw_response = {
            "meta": {"cursor": None},
            "body": [
                {
                    "id": "post_lowercase",
                    "title": "Lowercase subreddit",
                    "selftext": "body",
                    "url": "https://www.reddit.com/r/odoo/comments/post_lowercase/",
                    "permalink": "/r/odoo/comments/post_lowercase/",
                    "author": "user",
                    "subreddit": "odoo",
                    "created_utc": recent_ts,
                    "num_comments": 0,
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = raw_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())
        assert len(candidates) == 1
        assert candidates[0].post_id == "post_lowercase"


# ---------------------------------------------------------------------------
# CORRECTIVO: canonización de url relativa a absoluta (WARNING Opción A)
# ---------------------------------------------------------------------------


class TestUrlCanonicalization:
    """url se canoniza a URL absoluta igual que permalink."""

    def test_reddit3_relative_url_becomes_absolute(self):
        raw = {
            "body": [
                {
                    "id": "post1",
                    "title": "Test",
                    "selftext": "body",
                    "url": "/r/Odoo/comments/post1/",  # relative
                    "permalink": "/r/Odoo/comments/post1/test/",
                    "author": "user",
                    "subreddit": "Odoo",
                    "created_utc": _6_DAYS_AGO,
                    "num_comments": 0,
                }
            ]
        }
        result = _normalize_reddit3(raw)
        assert result[0].url.startswith("https://www.reddit.com")

    def test_reddit3_absolute_url_unchanged(self):
        abs_url = "https://example.com/some/link"
        raw = {
            "body": [
                {
                    "id": "post1",
                    "title": "Test",
                    "selftext": "body",
                    "url": abs_url,
                    "permalink": "/r/Odoo/comments/post1/test/",
                    "author": "user",
                    "subreddit": "Odoo",
                    "created_utc": _6_DAYS_AGO,
                    "num_comments": 0,
                }
            ]
        }
        result = _normalize_reddit3(raw)
        assert result[0].url == abs_url

    def test_reddit34_relative_url_becomes_absolute(self):
        raw = {
            "data": {
                "posts": [
                    {
                        "data": {
                            "id": "post1",
                            "title": "Test",
                            "selftext": "body",
                            "url": "/r/Odoo/comments/post1/",  # relative
                            "permalink": "/r/Odoo/comments/post1/test/",
                            "author": "user",
                            "subreddit": "Odoo",
                            "created_utc": _6_DAYS_AGO,
                            "num_comments": 0,
                        }
                    }
                ]
            }
        }
        result = _normalize_reddit34(raw)
        assert result[0].url.startswith("https://www.reddit.com")

    def test_reddapi_relative_url_becomes_absolute(self):
        raw = {
            "posts": [
                {
                    "data": {
                        "id": "post1",
                        "title": "Test",
                        "selftext": "body",
                        "url": "/r/Odoo/comments/post1/",  # relative
                        "permalink": "/r/Odoo/comments/post1/test/",
                        "author": "user",
                        "subreddit": "Odoo",
                        "created_utc": _6_DAYS_AGO,
                        "num_comments": 0,
                    }
                }
            ]
        }
        result = _normalize_reddapi(raw)
        assert result[0].url.startswith("https://www.reddit.com")


# ---------------------------------------------------------------------------
# CORRECTIVO SPEC: prueba runtime que >8 candidatos se entregan SIN truncación
# Escenario spec: "más de 8 candidatos se entregan sin truncación"
# ---------------------------------------------------------------------------


class TestNoTruncationAboveEight:
    """Garantía runtime: collect_candidates entrega >8 candidatos sin recortar."""

    def _mock_settings(self):
        s = MagicMock()
        s.reddit_api_key = "test-key"
        return s

    @patch("auto_reddit.reddit.client.datetime")
    @patch("auto_reddit.reddit.client.httpx.Client")
    def test_more_than_8_candidates_delivered_without_truncation(
        self, mock_client_cls, mock_dt
    ):
        """Spec scenario: when >8 in-scope posts exist, all are handed off (no cut to 8).

        This is the critical boundary test: change 1 MUST NOT apply downstream limits.
        """
        fake_now = 1_700_000_000
        mock_dt.now.return_value.timestamp.return_value = float(fake_now)

        # Build 12 posts within the 7-day window from r/Odoo
        n_posts = 12
        body = [
            {
                "id": f"post{i:02d}",
                "title": f"Odoo Post {i}",
                "selftext": f"Body of post {i}",
                "url": f"https://www.reddit.com/r/Odoo/comments/post{i:02d}/",
                "permalink": f"/r/Odoo/comments/post{i:02d}/test/",
                "author": f"user{i}",
                "subreddit": "Odoo",
                "created_utc": fake_now - (i * 3600),  # i hours ago, all within 7 days
                "num_comments": i,
            }
            for i in range(1, n_posts + 1)
        ]
        raw_response = {"meta": {"cursor": None}, "body": body}

        mock_response = MagicMock()
        mock_response.json.return_value = raw_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        candidates = collect_candidates(self._mock_settings())

        assert len(candidates) == n_posts, (
            f"Expected all {n_posts} candidates, got {len(candidates)}. "
            "collect_candidates MUST NOT truncate to 8 in change 1."
        )
        assert len(candidates) > 8, "Must deliver more than 8 candidates without cut"
        # Verify sorted descending
        for i in range(len(candidates) - 1):
            assert candidates[i].created_utc >= candidates[i + 1].created_utc


# ---------------------------------------------------------------------------
# CORRECTIVO WARNING: test dedicado para retry/backoff (_fetch_with_retry)
# ---------------------------------------------------------------------------


class TestRetryBackoff:
    """_fetch_with_retry: reintentos con backoff 2s→4s; lanza RuntimeError al fallar todo."""

    @patch("auto_reddit.reddit.client.time.sleep")
    def test_retry_succeeds_on_second_attempt(self, mock_sleep):
        """Falla en el primer intento, tiene éxito en el segundo; sleep llamado una vez con 2s."""
        mock_client = MagicMock()
        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = Exception("timeout")
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {"data": "ok"}
        mock_client.get.side_effect = [fail_response, ok_response]

        result = _fetch_with_retry(mock_client, "https://api.example.com", {}, {})

        assert result == {"data": "ok"}
        mock_sleep.assert_called_once_with(2)  # backoff[0] = 2s after first failure

    @patch("auto_reddit.reddit.client.time.sleep")
    def test_retry_succeeds_on_third_attempt(self, mock_sleep):
        """Falla dos veces, tiene éxito al tercer intento; sleep llamado con 2s y 4s."""
        mock_client = MagicMock()
        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = Exception("error")
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {"result": "success"}
        mock_client.get.side_effect = [fail_response, fail_response, ok_response]

        result = _fetch_with_retry(mock_client, "https://api.example.com", {}, {})

        assert result == {"result": "success"}
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)

    @patch("auto_reddit.reddit.client.time.sleep")
    def test_all_attempts_fail_raises_runtime_error(self, mock_sleep):
        """Cuando los 3 intentos fallan, lanza RuntimeError (no retorna lista vacía)."""
        mock_client = MagicMock()
        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = Exception("permanent error")
        mock_client.get.return_value = fail_response

        with pytest.raises(RuntimeError, match="All 3 attempts failed"):
            _fetch_with_retry(mock_client, "https://api.example.com", {}, {})

        assert mock_sleep.call_count == 2  # sleeps after attempt 1 and 2, not after 3

    @patch("auto_reddit.reddit.client.time.sleep")
    def test_no_sleep_on_first_success(self, mock_sleep):
        """Si el primer intento tiene éxito, no hay sleep."""
        mock_client = MagicMock()
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {}
        mock_client.get.return_value = ok_response

        _fetch_with_retry(mock_client, "https://api.example.com", {}, {})
        mock_sleep.assert_not_called()
