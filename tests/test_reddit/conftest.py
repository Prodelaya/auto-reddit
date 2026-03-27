"""Fixtures para tests del módulo reddit.

Carga snapshots sanitizados desde docs/integrations/reddit/*/raw/ (posts endpoints only).
Los fixtures exponen directamente el response_raw de cada proveedor.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_DOCS_ROOT = Path(__file__).parent.parent.parent / "docs" / "integrations" / "reddit"


def _load_latest_snapshot(provider: str, call_name: str) -> dict:
    """Carga el snapshot más reciente para un provider y call_name dados."""
    raw_dir = _DOCS_ROOT / provider / "raw"
    pattern = f"*{call_name}*.json"
    files = sorted(raw_dir.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(
            f"No snapshot found for {provider}/{call_name} in {raw_dir}"
        )
    with files[0].open() as f:
        full_snapshot = json.load(f)
    return full_snapshot["response_raw"]


@pytest.fixture()
def reddit3_posts_raw() -> dict:
    """response_raw de reddit3 subreddit_posts_new (shape plana en body[])."""
    return _load_latest_snapshot("reddit3", "subreddit_posts_new")


@pytest.fixture()
def reddit34_posts_raw() -> dict:
    """response_raw de reddit34 posts_by_subreddit_new (anidado en data.posts[].data)."""
    return _load_latest_snapshot("reddit34", "posts_by_subreddit_new")


@pytest.fixture()
def reddapi_posts_raw() -> dict:
    """response_raw de reddapi scrape_new_posts (anidado en posts[].data)."""
    return _load_latest_snapshot("reddapi", "scrape_new_posts")
