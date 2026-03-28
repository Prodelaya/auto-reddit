# Proposal: Runtime Documented Truth Alignment

## Intent

Cerrar cuatro derivas verificables entre la verdad documental vigente y el comportamiento ejecutable diario, para que producto, arquitectura y runtime expresen una unica verdad operativa mantenible.

## Scope

### In Scope
- Alinear la regla de ejecucion lunes-viernes con el runtime real.
- Hacer que `review_window_days` gobierne de verdad la ventana efectiva, o ajustar la documentacion minima si la verdad deseada fuese otra.
- Alinear `max_daily_opportunities` y cualquier limite diario efectivo con el comportamiento observable.
- Alinear el comportamiento del resumen diario, incluyendo el caso de 0 oportunidades.

### Out of Scope
- Refactors no relacionados, limpieza documental amplia o rediseño del pipeline archivado.
- Hardening de despliegue, `.env`, cron, CI o gobierno general de settings.
- Expansion funcional mas alla de las cuatro derivas cerradas.

## Approach

Usar `docs/product/product.md`, `docs/integrations/reddit/api-strategy.md` y `docs/architecture.md` como autoridad vigente, contrastar cada deriva contra el runtime actual y resolverla con el cambio minimo necesario: corregir ejecucion cuando la doc vigente sea la verdad deseada o ajustar la documentacion solo cuando esa correccion documental sea explicita y justificada.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auto_reddit/main.py` | Modified | Regla de ejecucion diaria y orquestacion del resumen. |
| `src/auto_reddit/config/` | Modified | Gobierno runtime de `review_window_days` y limites diarios. |
| `src/auto_reddit/delivery/` | Modified | Emision del resumen diario tambien con 0 oportunidades, si procede. |
| `docs/product/product.md` | Modified | Verdad funcional del flujo diario y resumen. |
| `docs/architecture.md` | Modified | Parametros operativos y responsabilidades del runtime. |
| `docs/integrations/reddit/api-strategy.md` | Modified | Regla operativa de lunes-viernes y limites vigentes. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mezclar alineamiento con feature work | Med | Mantener el inventario cerrado de cuatro derivas. |
| Corregir runtime sin cerrar la doc asociada | Med | Exigir una decision unica por deriva y verificarla en spec/verify. |

## Rollback Plan

Revertir los cambios del runtime y de documentacion de este change como una unidad para volver al estado previo sin dejar una nueva bifurcacion de verdad.

## Dependencies

- Discovery `openspec/discovery/runtime-documented-truth-alignment.md`
- Initiative `openspec/initiative/post-pipeline-alignment-hardening.md`

## Success Criteria

- [ ] Las cuatro derivas quedan resueltas con una sola verdad comprobable.
- [ ] La ejecucion de fin de semana deja de ser ambigua entre docs y runtime.
- [ ] `review_window_days` y los limites diarios efectivos dejan de ser knobs decorativos.
- [ ] El resumen diario queda alineado, incluido el caso de 0 oportunidades.
