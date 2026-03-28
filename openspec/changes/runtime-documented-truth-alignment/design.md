# Design: Runtime–Documented Truth Alignment

## Technical Approach

Close the four verified drifts between operational documentation and runtime with the minimum change per drift: add behavior where missing, replace hard-coded literals with their governing settings, and patch documentation only when the existing truth was incomplete. No new features, no refactors beyond these four sites.

## Architecture Decisions

| Decision | Choice | Alternative rejected | Rationale |
|----------|--------|---------------------|-----------|
| Weekend guard location | Early guard in `main.py:run()` before any side-effect | Cron-only guard | Docs explicitly say "esta lógica vive en `main.py`"; cron is external and out of scope |
| Review window source of truth | `settings.review_window_days` governs `collect_candidates()` cutoff | Keep hard-coded `_7_DAYS_SECONDS` constant | The setting exists but is decorative today; using it makes the parameter actually govern runtime |
| Daily delivery cap setting | Use `settings.max_daily_opportunities` as the single cap; remove `max_daily_deliveries` | Keep both settings | Two settings with identical default create split truth; docs reference only `max_daily_opportunities` |
| Zero-opportunity summary | Emit summary unconditionally on every executed weekday run | Keep current `if total_selected > 0` guard | Spec requires summary for 0-opportunity runs; docs §10 implies daily summary always |

## Data Flow

```
main.py:run()
    │
    ├── [NEW] Weekend guard → exit(0) if Sat/Sun
    │
    ├── collect_candidates(settings)
    │       └── cutoff_utc = now - (settings.review_window_days * 86400)
    │           ^^^ replaces hard-coded _7_DAYS_SECONDS
    │
    ├── ... (evaluation pipeline unchanged) ...
    │
    └── deliver_daily(store, settings)
            ├── cap = settings.max_daily_opportunities  (was max_daily_deliveries)
            └── render_summary() called ALWAYS on weekday runs
                 ^^^ including when selected == 0
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auto_reddit/main.py` | Modify | Add weekday guard at top of `run()` using `datetime.date.today().weekday()`. Exit before any pipeline work if Saturday (5) or Sunday (6). |
| `src/auto_reddit/reddit/client.py` | Modify | Replace `_7_DAYS_SECONDS` constant with `settings.review_window_days * 86400` in `collect_candidates()`. Remove or deprecate the hard-coded constant. Signature already receives `settings`. |
| `src/auto_reddit/config/settings.py` | Modify | Remove `max_daily_deliveries` field. `max_daily_opportunities` becomes the single cap. |
| `src/auto_reddit/delivery/__init__.py` | Modify | (1) Change `cap=settings.max_daily_deliveries` → `cap=settings.max_daily_opportunities`. (2) Move summary emission outside the `if total_selected > 0` guard so it fires on every executed run. Adapt `render_summary` call for count=0 case. |
| `src/auto_reddit/delivery/renderer.py` | Modify | Adjust `render_summary` to handle `count=0` gracefully (message text says "0 oportunidades hoy"). |
| `docs/product/product.md` | Modify | §7.3: clarify the 7-day window is governed by `review_window_days` setting. §10: state summary is always emitted, including 0-opportunity runs. |
| `docs/architecture.md` | Modify | §6: remove `max_daily_deliveries` from parameter list; confirm `max_daily_opportunities` is the single daily cap. |
| `docs/integrations/reddit/api-strategy.md` | Modify | §4/§11: confirm `review_window_days` governs the window and `max_daily_opportunities` is the single daily cap. |

## Interfaces / Contracts

No new interfaces. One removed setting:

```python
# settings.py — REMOVE
max_daily_deliveries: int = 8  # deleted; max_daily_opportunities is the single cap

# collect_candidates — CHANGE internal cutoff computation
cutoff_utc = now_utc - (settings.review_window_days * 86400)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Weekend guard returns early on Sat/Sun, proceeds on weekdays | Parametrize `run()` with mocked `date.today()` |
| Unit | `collect_candidates` uses `review_window_days` for cutoff | Pass settings with `review_window_days=3` and verify cutoff |
| Unit | `deliver_daily` uses `max_daily_opportunities` as cap | Existing selector tests; update fixtures to not pass `max_daily_deliveries` |
| Unit | Summary emitted when `total_selected == 0` | New test case in `test_deliver_daily.py` |
| Unit | `render_summary(count=0, …)` produces valid HTML | New case in `test_renderer.py` |
| Existing | Selector tests still pass with renamed cap arg | Run existing `test_selector.py` |

## Migration / Rollout

- `max_daily_deliveries` removal: if any `.env` file sets it, pydantic-settings `extra="ignore"` ensures no crash. The setting simply stops being read. Note in `.env.example` that `max_daily_opportunities` is the single cap.
- No data migration needed. No feature flags.

## Open Questions

None — all four drifts have a closed decision per the proposal and spec.
