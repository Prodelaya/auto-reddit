"""Extracción y normalización de comentarios por post con cadena de fallback.

Paso 3 del pipeline: enriquece los posts ya seleccionados aguas arriba con contexto
bruto normalizado del hilo. NO decide si un post es oportunidad ni aplica lógica de delivery.

Cadena de fallback por post (api-strategy.md):
    reddit34 → reddit3 → reddapi → None (post descartado)

ContextQuality asignada por proveedor:
    full     — reddit34 (árbol de replies, timestamps, sort=new)
    partial  — reddit3  (lista recursiva, created_utc, sin garantía de orden)
    degraded — reddapi  (flat, top comments, sin comment_id ni timestamps)
"""

from __future__ import annotations

import logging

import httpx

from auto_reddit.config.settings import Settings
from auto_reddit.reddit.client import _fetch_with_retry
from auto_reddit.shared.contracts import (
    ContextQuality,
    RedditCandidate,
    RedditComment,
    ThreadContext,
)

logger = logging.getLogger(__name__)

_REDDIT_BASE = "https://www.reddit.com"

_RAPIDAPI_HOST_REDDIT34 = "reddit34.p.rapidapi.com"
_RAPIDAPI_HOST_REDDIT3 = "reddit3.p.rapidapi.com"
_RAPIDAPI_HOST_REDDAPI = "reddapi.p.rapidapi.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_absolute_url(url: str) -> str:
    """Canoniza una URL a forma absoluta. Si es relativa, añade base de Reddit."""
    if url and not url.startswith("http"):
        return f"{_REDDIT_BASE}{url}"
    return url


def _strip_t1_prefix(comment_id: str) -> str:
    """Elimina el prefijo `t1_` que reddit34 incluye en los IDs de comentarios."""
    if comment_id and comment_id.startswith("t1_"):
        return comment_id[3:]
    return comment_id


# ---------------------------------------------------------------------------
# Per-provider comment normalizers
# ---------------------------------------------------------------------------


def _flatten_reddit34_comments(
    comments: list[dict], result: list[RedditComment] | None = None
) -> list[RedditComment]:
    """Aplana recursivamente el árbol de comentarios de reddit34.

    reddit34 expone replies como lista anidada dentro de cada comentario.
    Campos: id (t1_ prefixed), author, text, score, created (ISO 8601), permalink, parent_id, depth, replies[].
    """
    if result is None:
        result = []
    for item in comments:
        raw_id = item.get("id", "") or ""
        comment_id = _strip_t1_prefix(raw_id) or None

        raw_parent = item.get("parent_id", "") or ""
        parent_id = _strip_t1_prefix(raw_parent) if raw_parent else None

        body = item.get("text", "") or ""

        # created es ISO 8601, p.e. "2026-03-27T13:46:04.000000+0000"
        created_raw = item.get("created")
        created_utc: int | None = None
        if created_raw:
            try:
                from datetime import datetime, timezone

                dt = datetime.fromisoformat(created_raw.replace("+0000", "+00:00"))
                created_utc = (
                    int(dt.replace(tzinfo=timezone.utc).timestamp())
                    if dt.tzinfo is None
                    else int(dt.timestamp())
                )
            except Exception:  # noqa: BLE001
                created_utc = None

        permalink_raw = item.get("permalink", "") or ""
        permalink = _to_absolute_url(permalink_raw) if permalink_raw else None

        score_raw = item.get("score")
        score = int(score_raw) if score_raw is not None else None

        depth_raw = item.get("depth")
        depth = int(depth_raw) if depth_raw is not None else None

        result.append(
            RedditComment(
                comment_id=comment_id,
                author=item.get("author") or None,
                body=body,
                score=score,
                created_utc=created_utc,
                permalink=permalink,
                parent_id=parent_id if parent_id and parent_id != comment_id else None,
                depth=depth,
                source_api="reddit34",
            )
        )

        replies = item.get("replies") or []
        if replies:
            _flatten_reddit34_comments(replies, result)

    return result


def _normalize_comments_reddit34(raw: dict) -> list[RedditComment]:
    """Normaliza la respuesta de reddit34 /getPostCommentsWithSort.

    Estructura: data.comments[] con replies anidadas.
    """
    comments_raw = raw.get("data", {}).get("comments", [])
    return _flatten_reddit34_comments(comments_raw)


def _flatten_reddit3_comments(
    comments: list[dict], result: list[RedditComment] | None = None
) -> list[RedditComment]:
    """Aplana recursivamente el árbol de comentarios de reddit3.

    reddit3 expone post_comments[] con replies anidadas.
    Campos: id (sin prefijo), author, content, score, created_utc (unix), replies[].
    Sin permalink ni depth explícitos; sin parent_id explícito en el raw.
    """
    if result is None:
        result = []
    for item in comments:
        raw_id = item.get("id", "") or ""
        comment_id = raw_id or None

        body = item.get("content", "") or ""

        created_raw = item.get("created_utc")
        created_utc: int | None = int(created_raw) if created_raw is not None else None

        score_raw = item.get("score")
        score = int(score_raw) if score_raw is not None else None

        result.append(
            RedditComment(
                comment_id=comment_id,
                author=item.get("author") or None,
                body=body,
                score=score,
                created_utc=created_utc,
                permalink=None,
                parent_id=None,
                depth=None,
                source_api="reddit3",
            )
        )

        replies = item.get("replies") or []
        if replies:
            _flatten_reddit3_comments(replies, result)

    return result


def _normalize_comments_reddit3(raw: dict) -> list[RedditComment]:
    """Normaliza la respuesta de reddit3 /v1/reddit/post.

    Estructura: body.post_comments[] con replies anidadas.
    """
    post_comments = raw.get("body", {}).get("post_comments", [])
    return _flatten_reddit3_comments(post_comments)


def _normalize_comments_reddapi(raw: dict) -> list[RedditComment]:
    """Normaliza la respuesta de reddapi /api/scrape_post_comments.

    Estructura: comments[] — lista plana, sin comment_id, timestamps ni permalink.
    """
    comments_raw = raw.get("comments", [])
    result: list[RedditComment] = []
    for item in comments_raw:
        body = item.get("comment", "") or ""
        score_raw = item.get("score")
        score = int(score_raw) if score_raw is not None else None

        result.append(
            RedditComment(
                comment_id=None,
                author=item.get("author") or None,
                body=body,
                score=score,
                created_utc=None,
                permalink=None,
                parent_id=None,
                depth=None,
                source_api="reddapi",
            )
        )
    return result


# ---------------------------------------------------------------------------
# Per-provider comment fetchers
# ---------------------------------------------------------------------------


def _fetch_comments_reddit34(
    client: httpx.Client, post_id: str, permalink: str, headers: dict
) -> tuple[list[RedditComment], ContextQuality]:
    """Recupera comentarios vía reddit34 /getPostCommentsWithSort?sort=new.

    Retorna (comentarios, ContextQuality.full).
    Lanza excepción si la llamada falla (el fallback chain la captura).
    """
    url = f"https://{_RAPIDAPI_HOST_REDDIT34}/getPostCommentsWithSort"
    params = {"post_url": permalink, "sort": "new"}
    raw = _fetch_with_retry(client, url, headers, params)
    comments = _normalize_comments_reddit34(raw)
    return comments, ContextQuality.full


def _fetch_comments_reddit3(
    client: httpx.Client, post_id: str, permalink: str, headers: dict
) -> tuple[list[RedditComment], ContextQuality]:
    """Recupera comentarios vía reddit3 /v1/reddit/post?url=...

    Retorna (comentarios, ContextQuality.partial).
    Lanza excepción si la llamada falla.
    """
    url = f"https://{_RAPIDAPI_HOST_REDDIT3}/v1/reddit/post"
    params = {"url": permalink}
    raw = _fetch_with_retry(client, url, headers, params)
    comments = _normalize_comments_reddit3(raw)
    return comments, ContextQuality.partial


def _fetch_comments_reddapi(
    client: httpx.Client, post_id: str, permalink: str, headers: dict
) -> tuple[list[RedditComment], ContextQuality]:
    """Recupera comentarios vía reddapi /api/scrape_post_comments?post_url=...

    Retorna (comentarios, ContextQuality.degraded).
    Lanza excepción si la llamada falla.
    """
    url = f"https://{_RAPIDAPI_HOST_REDDAPI}/api/scrape_post_comments"
    params = {"post_url": permalink, "comments_num": "10"}
    raw = _fetch_with_retry(client, url, headers, params)
    comments = _normalize_comments_reddapi(raw)
    return comments, ContextQuality.degraded


# ---------------------------------------------------------------------------
# Per-post fallback chain
# ---------------------------------------------------------------------------


def _fetch_thread_context(
    candidate: RedditCandidate, api_key: str
) -> ThreadContext | None:
    """Intenta recuperar comentarios para un post con cadena de fallback.

    Orden: reddit34 → reddit3 → reddapi.
    Retorna None si todos los proveedores fallan (el post debe descartarse).
    Un post con 0 comentarios sigue siendo válido si el proveedor responde correctamente.
    """
    permalink = candidate.permalink

    headers_reddit34 = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDIT34,
        "Accept": "application/json",
    }
    headers_reddit3 = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDIT3,
        "Accept": "application/json",
    }
    headers_reddapi = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDAPI,
        "Accept": "application/json",
        "User-Agent": "RapidAPI Playground",  # Requerido: sin este header Cloudflare responde 403
    }

    providers: list[tuple[str, object]] = [
        ("reddit34", (headers_reddit34, _fetch_comments_reddit34)),
        ("reddit3", (headers_reddit3, _fetch_comments_reddit3)),
        ("reddapi", (headers_reddapi, _fetch_comments_reddapi)),
    ]

    with httpx.Client() as client:
        for provider_name, (headers, fetch_fn) in providers:
            try:
                logger.debug(
                    "Fetching comments for post %s via %s",
                    candidate.post_id,
                    provider_name,
                )
                comments, quality = fetch_fn(  # type: ignore[operator]
                    client, candidate.post_id, permalink, headers
                )
                logger.debug(
                    "Post %s: %d comments via %s (quality=%s)",
                    candidate.post_id,
                    len(comments),
                    provider_name,
                    quality.value,
                )
                return ThreadContext(
                    candidate=candidate,
                    comments=comments,
                    comment_count=len(comments),
                    quality=quality,
                    source_api=provider_name,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Comments provider %s failed for post %s: %s. Trying next…",
                    provider_name,
                    candidate.post_id,
                    exc,
                )

    logger.warning(
        "All comment providers failed for post %s. Dropping post from batch.",
        candidate.post_id,
    )
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def fetch_thread_contexts(
    candidates: list[RedditCandidate], settings: Settings
) -> list[ThreadContext]:
    """Enriquece la lista de candidatos seleccionados con contexto bruto del hilo.

    Solo procesa los posts de ``candidates`` (ya seleccionados aguas arriba).
    Descarta los posts en los que todos los proveedores fallen.
    Un post con 0 comentarios se entrega si el proveedor respondió correctamente.

    Args:
        candidates: Lista de posts seleccionados por el paso upstream.
        settings: Configuración con ``reddit_api_key``.

    Returns:
        Lista de ``ThreadContext`` para los posts que lograron contexto. Los posts
        con fallo total de todos los proveedores se descartan silenciosamente (log warning).
    """
    result: list[ThreadContext] = []
    dropped = 0

    for candidate in candidates:
        thread_ctx = _fetch_thread_context(candidate, settings.reddit_api_key)
        if thread_ctx is None:
            dropped += 1
        else:
            result.append(thread_ctx)

    if dropped:
        logger.warning(
            "Thread context extraction: %d/%d posts dropped (all providers failed).",
            dropped,
            len(candidates),
        )

    logger.info(
        "Thread context extraction complete: %d/%d posts enriched.",
        len(result),
        len(candidates),
    )
    return result
