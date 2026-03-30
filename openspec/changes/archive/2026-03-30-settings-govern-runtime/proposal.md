# Proposal: Alinear contrato documentado de settings con runtime

## Intent

Corregir el alcance del change: los settings ya gobiernan runtime. El objetivo real es alinear la superficie DOCUMENTADA con el contrato runtime verificado y eliminar ambigüedad semántica.

## Scope

### In Scope
- Documentar todos los settings que sí gobiernan runtime.
- Explicar explícitamente `daily_review_limit` como cap pre-IA y `max_daily_opportunities` como cap post-IA/entrega.
- Corregir referencias de `deepseek_model`, `db_path` y la nota de `DB_PATH` frente al default real.

### Out of Scope
- Cambios de comportamiento runtime o refactors en código.
- Renombrar settings, cambiar defaults o introducir knobs nuevos.

## Approach

Tomar `config/settings.py` y sus consumidores runtime como fuente de verdad, y actualizar `docs/architecture.md`, `docs/product/product.md` y `.env.example` para que describan el mismo contrato. La documentación debe distinguir el punto exacto del pipeline donde actúa cada límite diario.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docs/architecture.md` | Modified | Inventario y semántica exacta de settings |
| `docs/product/product.md` | Modified | Añadir `daily_review_limit` y su diferencia con entrega |
| `.env.example` | Modified | Aclarar `DB_PATH` y defaults/precedencia |
| `openspec/specs/daily-runtime-governance/spec.md` | Modified | Extender contrato documental si aplica |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Seguir confundiendo ambos límites diarios | Med | Describir pre-IA vs post-IA con el mismo vocabulario en todos los artefactos |
| Dejar documentación parcialmente alineada | Med | Actualizar product, architecture y example env en el mismo change |

## Rollback Plan

Revertir los cambios documentales y delta specs del change. No requiere rollback de datos ni runtime porque no altera comportamiento ejecutable.

## Dependencies

- Discovery brief `sdd/settings-govern-runtime/explore` ya corregido
- Contrato runtime vigente en `src/auto_reddit/config/settings.py`, `main.py`, `delivery/__init__.py`, `reddit/client.py`

## Success Criteria

- [ ] La documentación enumera solo settings con consumidor runtime real.
- [ ] `daily_review_limit` y `max_daily_opportunities` quedan diferenciados por punto de aplicación.
- [ ] `deepseek_model` y `db_path` aparecen documentados donde corresponda.
- [ ] `.env.example` no contradice el default real ni la precedencia operativa de `DB_PATH`.
