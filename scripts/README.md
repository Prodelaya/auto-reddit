# Scripts

`reddit_api_raw_snapshot.py` is technical exploration tooling.

- It calls the Reddit providers and endpoints currently relevant to `auto-reddit`.
- It stores one raw JSON snapshot per HTTP call under `docs/integrations/reddit/<provider>/raw/`.
- It is intentionally outside the functional product flow.

Run it with `uv`:

```bash
uv run python scripts/reddit_api_raw_snapshot.py --help
uv run python scripts/reddit_api_raw_snapshot.py --pages 2
```
