"""Capture raw Reddit API snapshots for technical exploration.

This script is research tooling. It calls the provider endpoints currently relevant
to auto-reddit, stores one JSON file per HTTP call, and keeps the raw payload so we
can validate response shape, batching and pagination behavior before design.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib import error, parse, request


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBREDDIT = "odoo"
DEFAULT_SUBREDDIT_URL = "https://www.reddit.com/r/Odoo/"
DEFAULT_POST_URL = "https://www.reddit.com/r/Odoo/comments/1s4l6x4/odoo_mcp_server/"
REDDAPI_USER_AGENT = "RapidAPI Playground"


@dataclass(frozen=True)
class SnapshotContext:
    subreddit: str
    subreddit_url: str
    post_url: str
    batch_size: int
    comment_limit: int
    search_query: str


@dataclass(frozen=True)
class EndpointSpec:
    provider: str
    call_name: str
    description: str
    base_url: str
    path: str
    raw_directory: Path
    pagination_key: str | None
    pagination_param: str | None
    params_factory: Callable[[SnapshotContext], dict[str, str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Call the currently relevant Reddit RapidAPI endpoints and save raw JSON "
            "snapshots under docs/integrations/reddit/<provider>/raw/."
        )
    )
    parser.add_argument(
        "--api-key", help="RapidAPI key. Defaults to REDDIT_API_KEY or .env."
    )
    parser.add_argument(
        "--subreddit", default=DEFAULT_SUBREDDIT, help="Target subreddit name."
    )
    parser.add_argument(
        "--subreddit-url",
        default=DEFAULT_SUBREDDIT_URL,
        help="Canonical subreddit URL used by providers that require a URL.",
    )
    parser.add_argument(
        "--post-url",
        default=DEFAULT_POST_URL,
        help="Representative Reddit post URL used for post-comment endpoints.",
    )
    parser.add_argument(
        "--search-query",
        default=DEFAULT_SUBREDDIT,
        help="Global search term for reddit-com exploratory calls.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Batch size for post listing endpoints that support it.",
    )
    parser.add_argument(
        "--comment-limit",
        type=int,
        default=10,
        help="Requested comment batch size for providers that support it.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Maximum pages to request when the provider returns a usable next-page token.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds.",
    )
    return parser.parse_args()


def build_context(args: argparse.Namespace) -> SnapshotContext:
    return SnapshotContext(
        subreddit=args.subreddit,
        subreddit_url=args.subreddit_url,
        post_url=args.post_url,
        batch_size=args.batch_size,
        comment_limit=args.comment_limit,
        search_query=args.search_query,
    )


def provider_directory(provider: str) -> Path:
    return REPO_ROOT / "docs" / "integrations" / "reddit" / provider / "raw"


def endpoint_specs() -> list[EndpointSpec]:
    return [
        EndpointSpec(
            provider="reddit3",
            call_name="subreddit_posts_new",
            description="Primary posts source for r/Odoo candidate collection.",
            base_url="https://reddit3.p.rapidapi.com",
            path="/v1/reddit/posts",
            raw_directory=provider_directory("reddit3"),
            pagination_key="meta.cursor",
            pagination_param=None,
            params_factory=lambda ctx: {
                "url": ctx.subreddit_url,
                "filter": "new",
            },
        ),
        EndpointSpec(
            provider="reddit3",
            call_name="post_with_comments",
            description="Fallback post + comments source for thread context extraction.",
            base_url="https://reddit3.p.rapidapi.com",
            path="/v1/reddit/post",
            raw_directory=provider_directory("reddit3"),
            pagination_key=None,
            pagination_param=None,
            params_factory=lambda ctx: {"url": ctx.post_url},
        ),
        EndpointSpec(
            provider="reddit3",
            call_name="subreddit_recent_comments",
            description="Exploratory subreddit comments endpoint kept for provider comparison.",
            base_url="https://reddit3.p.rapidapi.com",
            path="/v1/reddit/subreddit/comments",
            raw_directory=provider_directory("reddit3"),
            pagination_key="meta.cursor",
            pagination_param=None,
            params_factory=lambda ctx: {"subreddit": ctx.subreddit},
        ),
        EndpointSpec(
            provider="reddit34",
            call_name="posts_by_subreddit_new",
            description="Secondary posts source with sort=new verification.",
            base_url="https://reddit34.p.rapidapi.com",
            path="/getPostsBySubreddit",
            raw_directory=provider_directory("reddit34"),
            pagination_key="data.cursor",
            pagination_param=None,
            params_factory=lambda ctx: {
                "subreddit": ctx.subreddit,
                "sort": "new",
            },
        ),
        EndpointSpec(
            provider="reddit34",
            call_name="post_comments_new",
            description="Primary comments source with verified sort=new behavior.",
            base_url="https://reddit34.p.rapidapi.com",
            path="/getPostCommentsWithSort",
            raw_directory=provider_directory("reddit34"),
            pagination_key="data.cursor",
            pagination_param=None,
            params_factory=lambda ctx: {
                "post_url": ctx.post_url,
                "sort": "new",
            },
        ),
        EndpointSpec(
            provider="reddapi",
            call_name="scrape_new_posts",
            description="Posts fallback with explicit batch-size parameter.",
            base_url="https://reddapi.p.rapidapi.com",
            path="/api/scrape/new",
            raw_directory=provider_directory("reddapi"),
            pagination_key="cursor",
            pagination_param="cursor",
            params_factory=lambda ctx: {
                "subreddit": ctx.subreddit,
                "limit": str(ctx.batch_size),
            },
        ),
        EndpointSpec(
            provider="reddapi",
            call_name="new_comments_with_post_content",
            description="Fallback combined thread context endpoint; useful to compare semantics.",
            base_url="https://reddapi.p.rapidapi.com",
            path="/api/scrape_new_comments_and_its_post_content",
            raw_directory=provider_directory("reddapi"),
            pagination_key=None,
            pagination_param=None,
            params_factory=lambda ctx: {
                "post_url": ctx.post_url,
                "comments_num": str(ctx.comment_limit),
            },
        ),
        EndpointSpec(
            provider="reddapi",
            call_name="post_comments_simple",
            description="Auxiliary comment endpoint for contrast against the combined thread response.",
            base_url="https://reddapi.p.rapidapi.com",
            path="/api/scrape_post_comments",
            raw_directory=provider_directory("reddapi"),
            pagination_key=None,
            pagination_param=None,
            params_factory=lambda ctx: {
                "post_url": ctx.post_url,
                "comments_num": str(ctx.comment_limit),
            },
        ),
        EndpointSpec(
            provider="reddit-com",
            call_name="search_posts_new_week",
            description="Exploratory global search endpoint kept outside the main flow.",
            base_url="https://reddit-com.p.rapidapi.com",
            path="/posts/search-posts",
            raw_directory=provider_directory("reddit-com"),
            pagination_key="meta.nextPage",
            pagination_param="page",
            params_factory=lambda ctx: {
                "query": ctx.search_query,
                "sort": "new",
                "time": "week",
            },
        ),
    ]


def load_api_key(explicit_api_key: str | None) -> str | None:
    if explicit_api_key:
        return explicit_api_key

    env_value = os.getenv("REDDIT_API_KEY")
    if env_value:
        return env_value

    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "REDDIT_API_KEY":
            continue
        return value.strip().strip('"').strip("'")

    return None


def build_request_url(base_url: str, path: str, params: dict[str, str]) -> str:
    query_string = parse.urlencode(params, doseq=True)
    return f"{base_url}{path}?{query_string}" if query_string else f"{base_url}{path}"


def get_nested_value(payload: Any, dotted_path: str | None) -> Any:
    if dotted_path is None:
        return None

    current = payload
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def normalize_pagination_token(token: Any, param_name: str) -> str | None:
    if token in (None, ""):
        return None

    if isinstance(token, (int, float)):
        return str(token)

    if not isinstance(token, str):
        return None

    parsed = parse.urlparse(token)
    if parsed.scheme and parsed.netloc:
        values = parse.parse_qs(parsed.query).get(param_name)
        if values:
            return values[0]
        return token

    return token


def slugify(value: str) -> str:
    clean = []
    for character in value.lower():
        if character.isalnum():
            clean.append(character)
        else:
            clean.append("_")
    return "".join(clean).strip("_")


def save_snapshot(
    *,
    spec: EndpointSpec,
    timestamp: datetime,
    page_number: int,
    url: str,
    params: dict[str, str],
    request_headers: dict[str, str],
    status_code: int | None,
    duration_ms: int,
    response_url: str | None,
    response_headers: dict[str, str],
    payload: Any,
) -> Path:
    spec.raw_directory.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}_{slugify(spec.call_name)}"
        f"_page_{page_number:02d}.json"
    )
    destination = spec.raw_directory / filename
    document = {
        "provider": spec.provider,
        "endpoint": spec.path,
        "call_name": spec.call_name,
        "description": spec.description,
        "timestamp_utc": timestamp.isoformat(),
        "request": {
            "method": "GET",
            "url": url,
            "params": params,
            "headers": request_headers,
        },
        "response_status": status_code,
        "duration_ms": duration_ms,
        "response_url": response_url,
        "response_headers": response_headers,
        "response_raw": payload,
    }
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    return destination


def build_request_headers(spec: EndpointSpec, api_key: str) -> dict[str, str]:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": parse.urlparse(spec.base_url).netloc,
        "Accept": "application/json",
    }
    if spec.provider == "reddapi":
        headers["User-Agent"] = REDDAPI_USER_AGENT
    return headers


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() == "x-rapidapi-key":
            redacted[key] = "<redacted>"
            continue
        redacted[key] = value
    return redacted


def header_items_to_dict(items: Any) -> dict[str, str]:
    return {str(key): str(value) for key, value in items}


def fetch_endpoint(
    *,
    spec: EndpointSpec,
    context: SnapshotContext,
    api_key: str,
    page_limit: int,
    timeout: float,
) -> list[Path]:
    saved_files: list[Path] = []
    params = {key: str(value) for key, value in spec.params_factory(context).items()}

    for page_number in range(1, page_limit + 1):
        timestamp = datetime.now(UTC)
        url = build_request_url(spec.base_url, spec.path, params)
        request_headers = build_request_headers(spec, api_key)
        req = request.Request(
            url,
            headers=request_headers,
            method="GET",
        )

        started_at = time.perf_counter()
        status_code: int | None = None
        response_url: str | None = None
        response_headers: dict[str, str] = {}
        payload: Any
        try:
            with request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                response_url = response.geturl()
                response_headers = header_items_to_dict(response.getheaders())
                raw_body = response.read().decode("utf-8")
                payload = json.loads(raw_body)
        except error.HTTPError as exc:
            status_code = exc.code
            response_url = exc.geturl()
            response_headers = header_items_to_dict(exc.headers.items())
            raw_body = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw_body)
            except json.JSONDecodeError:
                payload = {"error_body": raw_body}
        except error.URLError as exc:
            payload = {"network_error": str(exc.reason)}
        except json.JSONDecodeError:
            payload = {"decode_error": "Response was not valid JSON."}

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        saved_files.append(
            save_snapshot(
                spec=spec,
                timestamp=timestamp,
                page_number=page_number,
                url=url,
                params=dict(params),
                request_headers=redact_headers(request_headers),
                status_code=status_code,
                duration_ms=duration_ms,
                response_url=response_url,
                response_headers=response_headers,
                payload=payload,
            )
        )

        if not spec.pagination_key or not spec.pagination_param:
            break

        next_token = normalize_pagination_token(
            get_nested_value(payload, spec.pagination_key),
            spec.pagination_param,
        )
        if not next_token:
            break
        params[spec.pagination_param] = next_token

    return saved_files


def main() -> int:
    args = parse_args()
    api_key = load_api_key(args.api_key)
    if not api_key:
        print(
            "Missing RapidAPI key. Pass --api-key or define REDDIT_API_KEY in the environment/.env.",
            file=sys.stderr,
        )
        return 1

    context = build_context(args)
    all_saved_files: list[Path] = []

    for spec in endpoint_specs():
        saved_files = fetch_endpoint(
            spec=spec,
            context=context,
            api_key=api_key,
            page_limit=max(args.pages, 1),
            timeout=args.timeout,
        )
        all_saved_files.extend(saved_files)
        for saved_file in saved_files:
            print(saved_file.relative_to(REPO_ROOT))

    print(f"Saved {len(all_saved_files)} snapshot files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
