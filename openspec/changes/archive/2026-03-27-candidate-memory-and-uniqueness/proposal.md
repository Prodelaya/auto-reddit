# Proposal: Candidate Memory and Uniqueness

## Intent

Cerrar el segundo slice del pipeline diario: aplicar memoria operativa minima y unicidad por post para que la revision diaria no reprocese decisiones finales y pueda reintentar Telegram sin volver a evaluar la IA.

## Scope

### In Scope
- Excluir antes de la revision los posts ya marcados como `sent` o `rejected`.
- Recortar la revision diaria a los 8 posts elegibles mas recientes por `created_at`.
- Persistir `rejected` como decision final y una persistencia operacional minima previa a `sent` para retry sin reevaluacion.
- Cerrar en `sent` solo tras entrega correcta en Telegram.

### Out of Scope
- Introducir estado `approved`, backlog editorial o persistencia de `not selected today`.
- Redisenar la recoleccion Reddit, el prompting IA o el mecanismo tecnico detallado de retries.

## Approach

Añadir una capa de memoria operativa minima entre la coleccion de candidatos y el delivery. Esa capa separa con claridad decisiones finales de negocio (`sent`, `rejected`) de una situacion transitoria de pre-envio, mantiene elegibles solo los posts sin decision final y conserva el resultado aceptado por IA para reintentar Telegram sin reabrir evaluacion.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auto_reddit/persistence/` | Modified | Memoria operativa minima y unicidad por post. |
| `src/auto_reddit/main.py` | Modified | Encadenado del recorte diario y cierre tras delivery. |
| `src/auto_reddit/evaluation/` | Modified | Handoff entre aceptacion IA y persistencia previa a `sent`. |
| `src/auto_reddit/delivery/` | Modified | Confirmacion de `sent` solo despues de entrega exitosa. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Marcar `sent` antes del exito real de Telegram | Med | Mantener `sent` exclusivamente como cierre post-delivery correcto. |
| Revaluar IA tras fallo de Telegram | Med | Conservar persistencia transitoria minima con retry-readiness. |
| Inflar alcance con backlog o estados extra | Low | Blindar propuesta con reglas explicitas de exclusiones. |

## Rollback Plan

Revertir esta capa y volver temporalmente al flujo sin memoria operativa, preservando la recoleccion previa y sin introducir estados parciales como definitivos.

## Dependencies

- Salida normalizada del change archivado `reddit-candidate-collection`.
- Verdad de producto en `docs/product/product.md` y `docs/product/ai-style.md`.

## Success Criteria

- [ ] La revision diaria excluye `sent` y `rejected` antes de evaluar.
- [ ] Solo se revisan los 8 elegibles mas recientes por `created_at`.
- [ ] Un rechazo final queda persistido como `rejected` y no vuelve a competir.
- [ ] Un fallo de Telegram tras aceptacion IA permite retry sin reevaluacion.
- [ ] `sent` solo se registra tras entrega correcta y no aparece estado `approved`.
