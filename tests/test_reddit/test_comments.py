"""Tests unitarios para reddit/comments.py.

Cubre:
- Normalización por proveedor (reddit34 tree, reddit3 recursive, reddapi flat)
- Calidad de degradación (full / partial / degraded)
- Cadena de fallback: reddit34 falla → reddit3 éxito → quality partial
- Cadena de fallback: todos fallan → None (post descartado)
- fetch_thread_contexts: 3 candidatos, 1 falla total → 2 ThreadContext en salida
- Post con 0 comentarios se entrega si el proveedor respondió correctamente
- Compatibilidad de campos opcionales (None) según proveedor
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auto_reddit.reddit.comments import (
    _fetch_thread_context,
    _normalize_comments_reddit34,
    _normalize_comments_reddit3,
    _normalize_comments_reddapi,
    fetch_thread_contexts,
)
from auto_reddit.shared.contracts import (
    ContextQuality,
    RedditCandidate,
    RedditComment,
    ThreadContext,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_candidate(post_id: str = "abc123") -> RedditCandidate:
    return RedditCandidate(
        post_id=post_id,
        title="Test post",
        selftext="Some body",
        url="https://www.reddit.com/r/Odoo/comments/abc123/test/",
        permalink="https://www.reddit.com/r/Odoo/comments/abc123/test/",
        author="testuser",
        subreddit="Odoo",
        created_utc=1_774_562_157,
        num_comments=5,
        source_api="reddit34",
    )


def _make_settings(api_key: str = "test-key") -> MagicMock:
    s = MagicMock()
    s.reddit_api_key = api_key
    return s


# ---------------------------------------------------------------------------
# reddit34 normalizer — árbol de replies (tree + timestamps)
# ---------------------------------------------------------------------------

# Snapshot-based fixture: estructura idéntica al raw de reddit34 /getPostCommentsWithSort
_REDDIT34_RAW = {
    "success": True,
    "data": {
        "cursor": None,
        "comments": [
            {
                "author": "user_a",
                "created": "2026-03-27T13:46:04.000000+0000",
                "depth": 0,
                "id": "t1_ocrsax8",
                "media": [],
                "parent_id": "",
                "permalink": "https://www.reddit.com/r/Odoo/comments/1s4l6x4/comment/ocrsax8/",
                "replies": [],
                "score": 1,
                "text": "Top-level comment A",
            },
            {
                "author": "user_b",
                "created": "2026-03-27T09:43:06.738000+0000",
                "depth": 0,
                "id": "t1_ocqqub4",
                "media": [],
                "parent_id": "",
                "permalink": "https://www.reddit.com/r/Odoo/comments/1s4l6x4/comment/ocqqub4/",
                "replies": [
                    {
                        "author": "user_c",
                        "created": "2026-03-27T11:59:54.273000+0000",
                        "depth": 1,
                        "id": "t1_ocr90ad",
                        "media": [],
                        "parent_id": "t1_ocqqub4",
                        "permalink": "https://www.reddit.com/r/Odoo/comments/1s4l6x4/comment/ocr90ad/",
                        "replies": [],
                        "score": 2,
                        "text": "Reply to B",
                    }
                ],
                "score": 1,
                "text": "Top-level comment B with reply",
            },
        ],
    },
}


class TestNormalizeCommentsReddit34:
    def test_produces_correct_count_with_nested_replies(self):
        """Árbol aplanado: 2 top-level + 1 reply = 3 comentarios."""
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        assert len(result) == 3

    def test_all_results_are_reddit_comment_instances(self):
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        assert all(isinstance(c, RedditComment) for c in result)

    def test_source_api_is_reddit34(self):
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        assert all(c.source_api == "reddit34" for c in result)

    def test_comment_id_has_no_t1_prefix(self):
        """El prefijo t1_ debe eliminarse del comment_id."""
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        assert all(
            c.comment_id is None or not c.comment_id.startswith("t1_") for c in result
        )

    def test_first_comment_fields(self):
        """Verifica campos del primer comentario top-level."""
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        first = result[0]
        assert first.comment_id == "ocrsax8"
        assert first.author == "user_a"
        assert first.body == "Top-level comment A"
        assert first.score == 1
        assert first.depth == 0
        assert (
            first.permalink
            == "https://www.reddit.com/r/Odoo/comments/1s4l6x4/comment/ocrsax8/"
        )

    def test_created_utc_parsed_from_iso8601(self):
        """created (ISO 8601) se convierte a unix timestamp entero."""
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        assert all(
            isinstance(c.created_utc, int) for c in result if c.created_utc is not None
        )

    def test_reply_parent_id_stripped_of_t1_prefix(self):
        """El parent_id de la reply debe ser 'ocqqub4', sin prefijo t1_."""
        result = _normalize_comments_reddit34(_REDDIT34_RAW)
        reply = next(c for c in result if c.comment_id == "ocr90ad")
        assert reply.parent_id == "ocqqub4"
        assert reply.depth == 1

    def test_empty_comments_list_returns_empty(self):
        raw = {"data": {"comments": []}}
        result = _normalize_comments_reddit34(raw)
        assert result == []

    def test_missing_data_key_returns_empty(self):
        result = _normalize_comments_reddit34({})
        assert result == []


# ---------------------------------------------------------------------------
# reddit3 normalizer — lista recursiva (flat+nesting via replies)
# ---------------------------------------------------------------------------

# Snapshot-based fixture: estructura de body.post_comments[] de reddit3
_REDDIT3_RAW = {
    "meta": {"totalComments": 3},
    "body": {
        "post": {"id": "1s4l6x4", "title": "Test post"},
        "post_comments": [
            {
                "id": "ocobl47",
                "author": "Codemarchant",
                "up_votes": 2,
                "score": 2,
                "likes": "",
                "created_utc": 1_774_567_283,
                "content": "Top comment with reply",
                "replies": [
                    {
                        "id": "ocpq9tw",
                        "author": "Codemarchant",
                        "up_votes": 5,
                        "score": 5,
                        "likes": "",
                        "created_utc": 1_774_585_089,
                        "content": "Reply to top comment",
                        "replies": [],
                    }
                ],
            },
            {
                "id": "oco5612",
                "author": "Rub3nC",
                "up_votes": 1,
                "score": 1,
                "likes": "",
                "created_utc": 1_774_565_279,
                "content": "Another top comment",
                "replies": [],
            },
        ],
    },
}


class TestNormalizeCommentsReddit3:
    def test_produces_correct_count_with_nested_replies(self):
        """2 top-level + 1 reply = 3 comentarios."""
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert len(result) == 3

    def test_all_results_are_reddit_comment_instances(self):
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert all(isinstance(c, RedditComment) for c in result)

    def test_source_api_is_reddit3(self):
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert all(c.source_api == "reddit3" for c in result)

    def test_body_mapped_from_content_field(self):
        """El campo `content` de reddit3 debe mapearse a `body`."""
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        bodies = {c.comment_id: c.body for c in result}
        assert bodies["ocobl47"] == "Top comment with reply"
        assert bodies["oco5612"] == "Another top comment"

    def test_created_utc_is_unix_int(self):
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert all(
            isinstance(c.created_utc, int) for c in result if c.created_utc is not None
        )

    def test_permalink_is_none(self):
        """reddit3 no expone permalink en comentarios."""
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert all(c.permalink is None for c in result)

    def test_depth_is_none(self):
        """reddit3 no expone depth explícito en comentarios."""
        result = _normalize_comments_reddit3(_REDDIT3_RAW)
        assert all(c.depth is None for c in result)

    def test_empty_post_comments_returns_empty(self):
        raw = {"body": {"post_comments": []}}
        result = _normalize_comments_reddit3(raw)
        assert result == []

    def test_missing_body_key_returns_empty(self):
        result = _normalize_comments_reddit3({})
        assert result == []


# ---------------------------------------------------------------------------
# reddapi normalizer — lista plana, top comments only
# ---------------------------------------------------------------------------

# Snapshot-based fixture: estructura de comments[] de reddapi /api/scrape_post_comments
_REDDAPI_RAW = {
    "success": True,
    "comments": [
        {
            "comment": "Peekaboo comment text",
            "author": "Codemarchant",
            "user_id": "t2_26c5dh7o51",
            "score": 2,
        },
        {
            "comment": "Another flat comment",
            "author": "Rub3nC",
            "user_id": "t2_69i5e",
            "score": 1,
        },
    ],
}


class TestNormalizeCommentsReddapi:
    def test_produces_correct_count(self):
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert len(result) == 2

    def test_all_results_are_reddit_comment_instances(self):
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert all(isinstance(c, RedditComment) for c in result)

    def test_source_api_is_reddapi(self):
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert all(c.source_api == "reddapi" for c in result)

    def test_comment_id_is_none(self):
        """reddapi no expone comment_id."""
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert all(c.comment_id is None for c in result)

    def test_created_utc_is_none(self):
        """reddapi no expone timestamps en comentarios."""
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert all(c.created_utc is None for c in result)

    def test_permalink_is_none(self):
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert all(c.permalink is None for c in result)

    def test_body_mapped_from_comment_field(self):
        """El campo `comment` de reddapi debe mapearse a `body`."""
        result = _normalize_comments_reddapi(_REDDAPI_RAW)
        assert result[0].body == "Peekaboo comment text"
        assert result[0].author == "Codemarchant"
        assert result[0].score == 2

    def test_empty_comments_returns_empty(self):
        result = _normalize_comments_reddapi({"comments": []})
        assert result == []

    def test_missing_comments_key_returns_empty(self):
        result = _normalize_comments_reddapi({})
        assert result == []


# ---------------------------------------------------------------------------
# Degradation indicator: quality per provider
# ---------------------------------------------------------------------------


class TestDegradationIndicator:
    """Verifica que ContextQuality se asigna correctamente por proveedor."""

    @patch("auto_reddit.reddit.comments.httpx.Client")
    def test_reddit34_success_returns_quality_full(self, mock_client_cls):
        """Si reddit34 tiene éxito, quality debe ser 'full'."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": True,
            "data": {"cursor": None, "comments": []},
        }
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        candidate = _make_candidate("post1")
        result = _fetch_thread_context(candidate, "test-key")

        assert result is not None
        assert result.quality == ContextQuality.full
        assert result.source_api == "reddit34"

    @patch("auto_reddit.reddit.comments._fetch_comments_reddit34")
    @patch("auto_reddit.reddit.comments.httpx.Client")
    def test_reddit3_fallback_returns_quality_partial(self, mock_client_cls, mock_r34):
        """Cuando reddit34 falla y reddit3 tiene éxito, quality debe ser 'partial'."""
        mock_r34.side_effect = RuntimeError("reddit34 failed")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "body": {
                "post_comments": [
                    {
                        "id": "cmt1",
                        "author": "user1",
                        "score": 1,
                        "created_utc": 1_774_567_283,
                        "content": "Some comment",
                        "replies": [],
                    }
                ]
            }
        }
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        candidate = _make_candidate("post2")
        result = _fetch_thread_context(candidate, "test-key")

        assert result is not None
        assert result.quality == ContextQuality.partial
        assert result.source_api == "reddit3"

    @patch("auto_reddit.reddit.comments._fetch_comments_reddit34")
    @patch("auto_reddit.reddit.comments._fetch_comments_reddit3")
    @patch("auto_reddit.reddit.comments.httpx.Client")
    def test_reddapi_fallback_returns_quality_degraded(
        self, mock_client_cls, mock_r3, mock_r34
    ):
        """Cuando reddit34 y reddit3 fallan, reddapi debe retornar quality 'degraded'."""
        mock_r34.side_effect = RuntimeError("reddit34 failed")
        mock_r3.side_effect = RuntimeError("reddit3 failed")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": True,
            "comments": [
                {"comment": "flat comment", "author": "user1", "score": 1},
            ],
        }
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        candidate = _make_candidate("post3")
        result = _fetch_thread_context(candidate, "test-key")

        assert result is not None
        assert result.quality == ContextQuality.degraded
        assert result.source_api == "reddapi"


# ---------------------------------------------------------------------------
# Fallback chain: all-fail → None (post dropped)
# ---------------------------------------------------------------------------


class TestFallbackChain:
    @patch("auto_reddit.reddit.comments._fetch_comments_reddit34")
    @patch("auto_reddit.reddit.comments._fetch_comments_reddit3")
    @patch("auto_reddit.reddit.comments._fetch_comments_reddapi")
    @patch("auto_reddit.reddit.comments.httpx.Client")
    def test_all_fail_returns_none(
        self, mock_client_cls, mock_reddapi, mock_r3, mock_r34
    ):
        """Cuando todos los proveedores fallan, _fetch_thread_context retorna None."""
        mock_r34.side_effect = RuntimeError("reddit34 down")
        mock_r3.side_effect = RuntimeError("reddit3 down")
        mock_reddapi.side_effect = RuntimeError("reddapi down")

        mock_client_cls.return_value.__enter__.return_value = MagicMock()

        candidate = _make_candidate("fail_post")
        result = _fetch_thread_context(candidate, "test-key")

        assert result is None

    @patch("auto_reddit.reddit.comments.httpx.Client")
    def test_reddit34_success_short_circuits(self, mock_client_cls):
        """Si reddit34 tiene éxito, no se llama a reddit3 ni a reddapi."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": True,
            "data": {"cursor": None, "comments": []},
        }
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        candidate = _make_candidate("short_post")
        result = _fetch_thread_context(candidate, "test-key")

        assert result is not None
        assert result.source_api == "reddit34"
        # Verificar que solo se hizo 1 llamada HTTP (reddit34)
        assert mock_client.get.call_count == 1


# ---------------------------------------------------------------------------
# fetch_thread_contexts: 3 candidatos, 1 falla total → 2 en salida
# ---------------------------------------------------------------------------


class TestFetchThreadContexts:
    @patch("auto_reddit.reddit.comments._fetch_thread_context")
    def test_drops_failed_posts_and_returns_successful_ones(self, mock_fetch_ctx):
        """3 candidatos: 1 falla total → 2 ThreadContext en salida."""
        c1 = _make_candidate("post1")
        c2 = _make_candidate("post2")
        c3 = _make_candidate("post3")

        ctx1 = ThreadContext(
            candidate=c1,
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit34",
        )
        ctx2 = ThreadContext(
            candidate=c2,
            comments=[],
            comment_count=0,
            quality=ContextQuality.partial,
            source_api="reddit3",
        )

        # post3 falla → None
        mock_fetch_ctx.side_effect = [ctx1, ctx2, None]

        settings = _make_settings()
        result = fetch_thread_contexts([c1, c2, c3], settings)

        assert len(result) == 2
        post_ids = {ctx.candidate.post_id for ctx in result}
        assert post_ids == {"post1", "post2"}

    @patch("auto_reddit.reddit.comments._fetch_thread_context")
    def test_post_with_zero_comments_is_delivered(self, mock_fetch_ctx):
        """Un post con 0 comentarios se entrega si el proveedor respondió correctamente."""
        candidate = _make_candidate("zero_comments")
        ctx = ThreadContext(
            candidate=candidate,
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit34",
        )
        mock_fetch_ctx.return_value = ctx

        settings = _make_settings()
        result = fetch_thread_contexts([candidate], settings)

        assert len(result) == 1
        assert result[0].comment_count == 0
        assert result[0].comments == []

    @patch("auto_reddit.reddit.comments._fetch_thread_context")
    def test_all_fail_returns_empty_list(self, mock_fetch_ctx):
        """Si todos los posts fallan, retorna lista vacía."""
        candidates = [_make_candidate(f"p{i}") for i in range(3)]
        mock_fetch_ctx.return_value = None

        settings = _make_settings()
        result = fetch_thread_contexts(candidates, settings)

        assert result == []

    @patch("auto_reddit.reddit.comments._fetch_thread_context")
    def test_only_selected_candidates_processed(self, mock_fetch_ctx):
        """Solo se procesan los candidatos recibidos; no se añaden posts externos."""
        c1 = _make_candidate("selected_post")
        ctx = ThreadContext(
            candidate=c1,
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit34",
        )
        mock_fetch_ctx.return_value = ctx

        settings = _make_settings()
        result = fetch_thread_contexts([c1], settings)

        # Solo se procesó el candidato recibido
        assert mock_fetch_ctx.call_count == 1
        assert mock_fetch_ctx.call_args[0][0].post_id == "selected_post"
        assert len(result) == 1

    @patch("auto_reddit.reddit.comments._fetch_thread_context")
    def test_thread_context_contains_no_business_decisions(self, mock_fetch_ctx):
        """ThreadContext no incluye clasificación de oportunidad ni acciones de entrega."""
        c1 = _make_candidate("post1")
        ctx = ThreadContext(
            candidate=c1,
            comments=[],
            comment_count=0,
            quality=ContextQuality.full,
            source_api="reddit34",
        )
        mock_fetch_ctx.return_value = ctx

        settings = _make_settings()
        result = fetch_thread_contexts([c1], settings)

        tc = result[0]
        # El contrato no expone campos de decisión de negocio
        assert not hasattr(tc, "is_opportunity")
        assert not hasattr(tc, "is_resolved")
        assert not hasattr(tc, "delivery_action")
        assert not hasattr(tc, "telegram_message")
