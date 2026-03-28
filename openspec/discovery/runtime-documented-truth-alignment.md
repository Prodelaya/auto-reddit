# Product Discovery Brief: runtime-documented-truth-alignment

## Problem Statement
- Confirmed: La documentacion vigente afirma que el sistema solo ejecuta de lunes a viernes y que esa logica vive en `main.py` (`docs/product/product.md:53`, `docs/integrations/reddit/api-strategy.md:185`), pero `src/auto_reddit/main.py` no aplica ningun guard de fin de semana.
- Confirmed: La arquitectura y el producto se presentan como verdad vigente, pero hoy hay divergencias observables entre lo documentado y lo que el runtime realmente hace.
- Inferred: Mientras esa brecha siga abierta, cualquier cambio posterior parte de una base ambigua: no queda claro si hay que cambiar runtime o reescribir verdad documental.
- Confirmed: El scope debe quedarse en las derivas funcionales ya identificadas: guard de fin de semana, `review_window_days` gobernando runtime, `max_daily_opportunities`/limites reales alineados y comportamiento del resumen diario.

## Goal / Desired Outcome
- Confirmed: El runtime debe comportarse segun la verdad documental vigente, o bien la verdad documental debe ajustarse de forma deliberada y minima cuando el comportamiento actual sea el deseado.
- Confirmed: Este change debe cerrar primero las divergencias funcionales explicitas y verificables, no reabrir decisiones de producto ya archivadas.
- Inferred: El resultado esperado es una unica verdad operativa legible desde docs y comprobable en runtime.
- Confirmed: El resumen diario tambien debe existir cuando haya cero oportunidades; runtime y documentacion deben reflejarlo igual.

## Primary Actor(s)
- Confirmed: Equipo de desarrollo y mantenimiento del pipeline.
- Inferred: Equipo operativo que necesita confiar en que la ejecucion real coincide con lo documentado.
- Pending: Ninguno.

## Stakeholders
- Desarrollo
- Operaciones
- Responsable del producto/documentacion

## Trigger
- Confirmed: Se detecta una divergencia entre verdad documental vigente y comportamiento runtime observable.
- Confirmed: Este trabajo llega despues del juicio del repo y antes de endurecer despliegue, CI o settings.

## Main Flow
1. Identificar la verdad documental vigente que gobierna el runtime diario.
2. Listar las divergencias funcionales observables entre esa verdad y el comportamiento actual.
3. Corregir el runtime para que cumpla la verdad vigente, o corregir la documentacion cuando el runtime actual sea la verdad deseada.
4. Dejar cada decision reflejada con criterios verificables para evitar nuevas bifurcaciones.

## Alternative Flows / Edge Cases
- Confirmed: Si una regla documentada ya no representa la operativa real deseada, el change puede resolverlo actualizando la documentacion en vez del runtime, pero solo de forma explicita y justificada.
- Confirmed: Los cambios puramente de arquitectura de informacion documental quedan fuera; eso vive en `docs-information-architecture-cleanup`.
- Confirmed: El resumen diario en dias sin oportunidades forma parte explicita del alineamiento funcional de este change.

## Business Rules
- Confirmed: La fuente de verdad vigente es `docs/product/product.md` + `docs/integrations/reddit/api-strategy.md` + `docs/architecture.md`.
- Confirmed: No se reabren decisiones cerradas del pipeline principal salvo para alinear runtime y verdad vigente.
- Confirmed: El change debe mantenerse unico y acotado a divergencias funcionales runtime-vs-docs.
- Confirmed: El inventario funcional de este change queda cerrado en cuatro derivas: fin de semana, `review_window_days`, `max_daily_opportunities`/limites reales y resumen diario.
- Inferred: Las contradicciones historicas de `TFM/` no son por si mismas criterio de alcance salvo que induzcan a error sobre la operativa vigente.

## Permissions / Visibility
- Confirmed: Cambio interno sin impacto en permisos de usuario final.
- Pending: Ninguno.

## Scope In
- Confirmed: Regla de ejecucion solo lunes-viernes donde la documentacion afirma que vive en `main.py`.
- Confirmed: `review_window_days` debe gobernar el runtime real, no quedarse como setting decorativo.
- Confirmed: `max_daily_opportunities` y cualquier limite efectivo diario deben quedar alineados con el comportamiento real.
- Confirmed: El resumen diario debe emitirse tambien con cero oportunidades si esa es la verdad documental vigente.
- Inferred: Ajustes minimos de documentacion solo cuando sean necesarios para cerrar la verdad correcta del comportamiento.

## Scope Out
- Confirmed: Hardening de `.env`, volumen SQLite, cron externo o contrato operativo de despliegue.
- Confirmed: CI.
- Confirmed: Reordenacion amplia de documentacion.
- Confirmed: Refactors de configuracion para hacer que todos los settings gobiernen runtime mas alla de `review_window_days` y `max_daily_opportunities`.

## Acceptance Criteria
- [ ] Existe un inventario cerrado de cuatro divergencias funcionales entre runtime y verdad documental vigente.
- [ ] Cada divergencia del inventario queda resuelta con una unica verdad: runtime alineado o documentacion ajustada deliberadamente.
- [ ] La regla de ejecucion en fin de semana deja de ser ambigua entre docs y runtime.
- [ ] `review_window_days` gobierna efectivamente la ventana real evaluada por runtime, o la documentacion queda ajustada de forma explicita.
- [ ] `max_daily_opportunities` y los limites diarios efectivos dejan de ser ambiguos entre docs y runtime.
- [ ] El comportamiento del resumen diario queda explicitamente alineado entre docs y runtime.

## Non-Functional Notes
- Confirmed: Debe reducir ambiguedad, no aumentarla con nuevas fuentes de verdad.
- Inferred: La verificacion ideal es automatizable, pero el detalle de testing pertenece a fases posteriores.

## Assumptions
- Confirmed: La documentacion vigente citada es la autoridad correcta hoy.
- Confirmed: El pipeline funcional archivado no necesita redisenarse para cerrar estas brechas.

## Open Decisions
- Ninguna.

## Risks
- Confirmed: Mezclar contradicciones historicas con verdad vigente puede inflar el alcance y convertir este change en limpieza documental general.
- Inferred: Si se corrige runtime sin cerrar la regla documental asociada, la ambiguedad reaparece rapido.

## Readiness for SDD
Status: ready-for-sdd
Reason: Ya estan cerrados el inventario funcional minimo y la regla del resumen diario, asi que el change tiene frontera concreta y criterios suficientes para pasar a proposal/spec cuando toque.
