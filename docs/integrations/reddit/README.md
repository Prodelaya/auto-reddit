# Reddit Integrations

This folder contains external integration documentation for unofficial Reddit APIs.

## APIs

- `reddit3` - https://rapidapi.com/sparior/api/reddit3
- `reddit34` - https://rapidapi.com/socialminer/api/reddit34
- `reddapi` - https://rapidapi.com/SeasonedCode/api/reddapi
- `reddit-com` - https://rapidapi.com/things4u-api4upro/api/reddit-com

## Documents

- [`comparison.md`](comparison.md) — Comparativa de cobertura, autenticacion, limites y utilidad de cada API
- [`api-strategy.md`](api-strategy.md) — Plan de estrategia: asignacion de APIs, cadena de fallback, cuotas, normalizacion y retry policy

Each `raw/` folder is intended for raw documentation, screenshots, or unprocessed examples.

## Exploration tooling

Use `scripts/reddit_api_raw_snapshot.py` to capture fresh raw JSON snapshots for the provider endpoints that matter right now.

What it does:

- Calls the current post, comment, and comparison endpoints for `reddit3`, `reddit34`, `reddapi`, and `reddit-com`
- Writes one JSON file per HTTP call into each provider `raw/` folder
- Preserves request metadata, execution timestamp, and the untouched API payload for later analysis

Run it with `uv`:

```bash
uv run python scripts/reddit_api_raw_snapshot.py --help
uv run python scripts/reddit_api_raw_snapshot.py --pages 2
```

Notes:

- The script reads `REDDIT_API_KEY` from the environment or `.env`, unless `--api-key` is passed explicitly.
- Use `--post-url` to point the comment endpoints at a different representative Reddit thread.
- Only endpoints with a known next-page parameter can be paged automatically; for the rest, the saved cursor still lets you inspect pagination behavior manually.
