"""Shared constants and helpers for Reddit API clients."""

_REDDIT_BASE = "https://www.reddit.com"

_RAPIDAPI_HOST_REDDIT3 = "reddit3.p.rapidapi.com"
_RAPIDAPI_HOST_REDDIT34 = "reddit34.p.rapidapi.com"
_RAPIDAPI_HOST_REDDAPI = "reddapi.p.rapidapi.com"


def _to_absolute_url(url: str) -> str:
    """Canonizes a URL to absolute form. If relative, prepends Reddit base."""
    if url and not url.startswith("http"):
        return f"{_REDDIT_BASE}{url}"
    return url
