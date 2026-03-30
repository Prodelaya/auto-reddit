"""Cliente Reddit: conecta con las APIs REST, trae posts y normaliza al contrato compartido."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone

import httpx

from auto_reddit.config.settings import Settings
from auto_reddit.reddit._constants import (
    _RAPIDAPI_HOST_REDDAPI,
    _RAPIDAPI_HOST_REDDIT3,
    _RAPIDAPI_HOST_REDDIT34,
    _to_absolute_url,
)
from auto_reddit.shared.contracts import RedditCandidate

logger = logging.getLogger(__name__)


def _normalize_reddit3(raw_json: dict) -> list[RedditCandidate]:
    """Normaliza la respuesta plana de reddit3 (/v1/reddit/posts).

    Posts con campo 'id' ausente se conservan con post_id vacío → is_complete=False.
    """
    candidates: list[RedditCandidate] = []
    for item in raw_json.get("body", []):
        permalink = _to_absolute_url(item.get("permalink", ""))
        url = _to_absolute_url(item.get("url", ""))
        created_utc = item.get("created_utc")
        candidates.append(
            RedditCandidate(
                post_id=str(item.get("id", "")),  # empty string → is_complete=False
                title=item.get("title") or "",
                selftext=item.get("selftext") or None,
                url=url,
                permalink=permalink,
                author=item.get("author") or None,
                subreddit=item.get("subreddit") or "",
                created_utc=int(created_utc) if created_utc is not None else 0,
                num_comments=item.get("num_comments"),
                source_api="reddit3",
            )
        )
    return candidates


def _normalize_reddit34(raw_json: dict) -> list[RedditCandidate]:
    """Normaliza la respuesta anidada de reddit34 (/getPostsBySubreddit).

    Estructura: data.posts[].data
    Posts con campo 'id' ausente se conservan con post_id vacío → is_complete=False.
    """
    candidates: list[RedditCandidate] = []
    posts = raw_json.get("data", {}).get("posts", [])
    for post in posts:
        item = post.get("data", {})
        post_id = str(item.get("id", ""))
        # Strip t3_ prefix if present (should not appear in id field, but guard anyway)
        if post_id.startswith("t3_"):
            post_id = post_id[3:]
        permalink = _to_absolute_url(item.get("permalink", ""))
        url = _to_absolute_url(item.get("url", ""))
        created_utc = item.get("created_utc")
        candidates.append(
            RedditCandidate(
                post_id=post_id,
                title=item.get("title") or "",
                selftext=item.get("selftext") or None,
                url=url,
                permalink=permalink,
                author=item.get("author") or None,
                subreddit=item.get("subreddit") or "",
                created_utc=int(created_utc) if created_utc is not None else 0,
                num_comments=item.get("num_comments"),
                source_api="reddit34",
            )
        )
    return candidates


def _normalize_reddapi(raw_json: dict) -> list[RedditCandidate]:
    """Normaliza la respuesta de reddapi (/api/scrape/new).

    Estructura: posts[].data
    Posts con campo 'id' ausente se conservan con post_id vacío → is_complete=False.
    """
    candidates: list[RedditCandidate] = []
    for post in raw_json.get("posts", []):
        item = post.get("data", {})
        post_id = str(item.get("id", ""))
        # Strip t3_ prefix if present
        if post_id.startswith("t3_"):
            post_id = post_id[3:]
        permalink = _to_absolute_url(item.get("permalink", ""))
        url = _to_absolute_url(item.get("url", ""))
        created_utc = item.get("created_utc")
        candidates.append(
            RedditCandidate(
                post_id=post_id,
                title=item.get("title") or "",
                selftext=item.get("selftext") or None,
                url=url,
                permalink=permalink,
                author=item.get("author") or None,
                subreddit=item.get("subreddit") or "",
                created_utc=int(created_utc) if created_utc is not None else 0,
                num_comments=item.get("num_comments"),
                source_api="reddapi",
            )
        )
    return candidates


# ---------------------------------------------------------------------------
# Cursor extractors per provider
# ---------------------------------------------------------------------------


def _cursor_reddit3(raw_json: dict) -> str | None:
    return raw_json.get("meta", {}).get("cursor") or None


def _cursor_reddit34(raw_json: dict) -> str | None:
    return raw_json.get("data", {}).get("cursor") or None


def _cursor_reddapi(raw_json: dict) -> str | None:
    return raw_json.get("cursor") or None


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2
_RETRY_BACKOFF = [2, 4]  # seconds between attempt 1→2, 2→3


def _fetch_with_retry(
    client: httpx.Client, url: str, headers: dict, params: dict
) -> dict:
    """GET with up to _MAX_RETRIES retries and linear backoff with fixed delays. Raises on all-fail."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF[attempt]
                logger.warning(
                    "Request to %s failed (attempt %d/%d): %s. Retrying in %ds…",
                    url,
                    attempt + 1,
                    _MAX_RETRIES + 1,
                    exc,
                    wait,
                )
                time.sleep(wait)
    raise RuntimeError(
        f"All {_MAX_RETRIES + 1} attempts failed for {url}"
    ) from last_exc


# ---------------------------------------------------------------------------
# Cursor-based pagination loop
# ---------------------------------------------------------------------------


def _paginate(
    client: httpx.Client,
    url: str,
    headers: dict,
    base_params: dict,
    cursor_param: str,
    normalizer: Callable[[dict], list[RedditCandidate]],
    cursor_extractor: Callable[[dict], str | None],
    cutoff_utc: int,
) -> list[RedditCandidate]:
    """Fetches pages until oldest post in page is outside the configured review window or no cursor.

    Returns all posts found (pre-filter; caller applies final review-window filter).
    """
    all_candidates: list[RedditCandidate] = []
    cursor: str | None = None

    while True:
        params = dict(base_params)
        if cursor:
            params[cursor_param] = cursor

        raw = _fetch_with_retry(client, url, headers, params)
        page_candidates = normalizer(raw)

        if not page_candidates:
            break

        all_candidates.extend(page_candidates)

        # Stop if oldest post in this page is before cutoff
        oldest_utc = min(c.created_utc for c in page_candidates)
        if oldest_utc < cutoff_utc:
            break

        next_cursor = cursor_extractor(raw)
        if not next_cursor:
            break

        cursor = next_cursor

    return all_candidates


# ---------------------------------------------------------------------------
# Provider strategies
# ---------------------------------------------------------------------------


def _collect_via_reddit3(api_key: str, cutoff_utc: int) -> list[RedditCandidate]:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDIT3,
        "Accept": "application/json",
    }
    with httpx.Client() as client:
        return _paginate(
            client=client,
            url=f"https://{_RAPIDAPI_HOST_REDDIT3}/v1/reddit/posts",
            headers=headers,
            base_params={"url": "https://www.reddit.com/r/Odoo/", "filter": "new"},
            cursor_param="cursor",
            normalizer=_normalize_reddit3,
            cursor_extractor=_cursor_reddit3,
            cutoff_utc=cutoff_utc,
        )


def _collect_via_reddit34(api_key: str, cutoff_utc: int) -> list[RedditCandidate]:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDIT34,
        "Accept": "application/json",
    }
    with httpx.Client() as client:
        return _paginate(
            client=client,
            url=f"https://{_RAPIDAPI_HOST_REDDIT34}/getPostsBySubreddit",
            headers=headers,
            base_params={"subreddit": "odoo", "sort": "new"},
            cursor_param="cursor",
            normalizer=_normalize_reddit34,
            cursor_extractor=_cursor_reddit34,
            cutoff_utc=cutoff_utc,
        )


def _collect_via_reddapi(api_key: str, cutoff_utc: int) -> list[RedditCandidate]:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST_REDDAPI,
        "Accept": "application/json",
        "User-Agent": "RapidAPI Playground",  # Required: without this header, returns 403
    }
    with httpx.Client() as client:
        return _paginate(
            client=client,
            url=f"https://{_RAPIDAPI_HOST_REDDAPI}/api/scrape/new",
            headers=headers,
            base_params={"subreddit": "odoo", "limit": "25"},
            cursor_param="cursor",
            normalizer=_normalize_reddapi,
            cursor_extractor=_cursor_reddapi,
            cutoff_utc=cutoff_utc,
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def collect_candidates(settings: Settings) -> list[RedditCandidate]:
    """Collect all r/Odoo posts within the configured review window using fallback chain.

    Strategy: reddit3 → reddit34 → reddapi. First successful provider wins.
    On all-fail: logs error and returns empty list.

    The review window is governed by ``settings.review_window_days``.

    Returns list sorted descending by created_utc. No cut to 8 applied here.
    """
    now_utc = int(datetime.now(tz=timezone.utc).timestamp())
    cutoff_utc = now_utc - (settings.review_window_days * 86400)

    providers: list[tuple[str, Callable]] = [
        ("reddit3", lambda: _collect_via_reddit3(settings.reddit_api_key, cutoff_utc)),
        (
            "reddit34",
            lambda: _collect_via_reddit34(settings.reddit_api_key, cutoff_utc),
        ),
        ("reddapi", lambda: _collect_via_reddapi(settings.reddit_api_key, cutoff_utc)),
    ]

    for provider_name, provider_fn in providers:
        try:
            logger.info("Trying provider: %s", provider_name)
            raw_candidates = provider_fn()

            # Apply review window filter (governed by settings.review_window_days)
            candidates = [c for c in raw_candidates if c.created_utc >= cutoff_utc]

            # Explicit subreddit guard: only r/Odoo posts, case-insensitive
            candidates = [c for c in candidates if c.subreddit.lower() == "odoo"]

            # Sort descending by created_utc (most recent first)
            candidates.sort(key=lambda c: c.created_utc, reverse=True)

            logger.info(
                "Provider %s returned %d candidates within %d-day window",
                provider_name,
                len(candidates),
                settings.review_window_days,
            )
            return candidates

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Provider %s failed: %s. Trying next provider…", provider_name, exc
            )

    logger.error("All providers failed. Returning empty candidate list.")
    return []
