# Tasks: Runtime–Documented Truth Alignment

## Phase 1: Configuration & Foundation

- [x] 1.1 Remove `max_daily_deliveries` field from `src/auto_reddit/config/settings.py`. Confirm `max_daily_opportunities` remains as single cap. Verify `model_config` has `extra="ignore"` for safe rollout.
- [x] 1.2 Update `.env.example` to remove/comment `max_daily_deliveries` and annotate `max_daily_opportunities` as the single daily cap.

## Phase 2: Core Runtime Fixes (4 drifts)

- [x] 2.1 **Weekend guard** — Add early weekday check at top of `run()` in `src/auto_reddit/main.py`: if `datetime.date.today().weekday() >= 5`, log skip reason and `return` before any pipeline side-effects (collection, evaluation, delivery).
- [x] 2.2 **Review window** — In `src/auto_reddit/reddit/client.py`, replace hard-coded `_7_DAYS_SECONDS` constant with `settings.review_window_days * 86400` inside `collect_candidates()`. Remove or deprecate the constant.
- [x] 2.3 **Delivery cap** — In `src/auto_reddit/delivery/__init__.py`, change cap source from `settings.max_daily_deliveries` to `settings.max_daily_opportunities`.
- [x] 2.4 **Unconditional summary** — In `src/auto_reddit/delivery/__init__.py`, move `render_summary()` call outside the `if total_selected > 0` guard so it fires on every executed weekday run (including 0-opportunity runs).
- [x] 2.5 **Renderer 0-count** — In `src/auto_reddit/delivery/renderer.py`, handle `count=0` in `render_summary` producing valid HTML (e.g. "0 oportunidades hoy").

## Phase 3: Documentation Patches

- [x] 3.1 `docs/product/product.md` — §7.3: clarify window governed by `review_window_days`. §10: summary always emitted including 0-opportunity runs.
- [x] 3.2 `docs/architecture.md` — §6: remove `max_daily_deliveries`; confirm single cap is `max_daily_opportunities`.
- [x] 3.3 `docs/integrations/reddit/api-strategy.md` — §4/§11: confirm `review_window_days` governs window; `max_daily_opportunities` is single cap.

## Phase 4: Testing & Verification

- [x] 4.1 Unit test: weekend guard — parametrize `run()` with mocked `date.today()` for Sat, Sun (skip) and Wed (proceed). Verify no collection/evaluation/delivery calls on weekend. *(Spec scenario: Weekend run is skipped cleanly)*
- [x] 4.2 Unit test: `review_window_days` cutoff — pass `settings.review_window_days=3`, verify `collect_candidates` cutoff excludes day-4 candidate, includes day-2. *(Spec scenarios: Shorter/Larger configured window)*
- [x] 4.3 Unit test: delivery cap — verify selector uses `max_daily_opportunities` (8→8 selected from 10; 3→3 selected from 5). Update fixtures that referenced `max_daily_deliveries`. *(Spec scenarios: Runtime enforces configured cap / Lowering cap)*
- [x] 4.4 Unit test: 0-opportunity summary — in `test_deliver_daily`, verify summary is emitted when 0 candidates selected. *(Spec scenario: Zero-opportunity weekday run)*
- [x] 4.5 Unit test: `render_summary(count=0)` produces valid HTML output. *(Renderer 0-count case)*
- [x] 4.6 Unit test: summary failure non-blocking — verify that when summary send raises, opportunity deliveries still proceed. *(Spec scenario: Summary failure does not stop deliveries)*
- [x] 4.7 Run full suite: `uv run pytest tests/ -x --tb=short` — all existing + new tests green.

## Post-Verify Corrective Pass (warnings from verify-report)

- [x] C.1 `docs/product/product.md §7.5` — replace hardcoded "8 oportunidades al día" with `max_daily_opportunities` as single cap truth.
- [x] C.2 `src/auto_reddit/main.py:87` — update stale `max_daily_deliveries` comment to `max_daily_opportunities`.
- [x] C.3 `src/auto_reddit/reddit/client.py` — remove unused `_7_DAYS_SECONDS` constant; update `_paginate` docstring and inline comment from "7-day window" to "configured review window".

## Post-Verify Wording Cleanup (final wording alignment flagged by second verify)

- [x] W.1 `src/auto_reddit/main.py:39` — update comment from "ventana 7 días, sin recorte" to "ventana configurada por review_window_days, sin recorte".
- [x] W.2 `docs/product/product.md §7.4` — replace two occurrences of "ventana de 7 días" with "ventana configurada por `review_window_days`".
