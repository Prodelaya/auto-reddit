# Product Discovery Brief: settings-govern-runtime

## Problem Statement
- Confirmed: `src/auto_reddit/config/settings.py` expone settings que no gobiernan hoy el runtime real.
- Confirmed: `review_window_days` existe como setting, pero `src/auto_reddit/reddit/client.py` calcula el cutoff con `_7_DAYS_SECONDS` hardcodeado y comentarios de "7-day window".
- Confirmed: `max_daily_opportunities` sigue existiendo en `Settings` y en documentacion (`docs/architecture.md`, `docs/integrations/reddit/api-strategy.md`), pero el runtime no lo consume; los caps efectivos pasan por `daily_review_limit` y `max_daily_deliveries`.
- Inferred: Mientras existan knobs documentados pero ignorados, la configuracion publica del sistema miente sobre lo que controla realmente.

## Goal / Desired Outcome
- Confirmed: Conseguir que los settings soportados gobiernen de verdad el runtime.
- Confirmed: Si un knob no debe gobernar nada, debe salir del contrato soportado en vez de seguir aparentando configurabilidad.
- Inferred: El resultado esperado es una superficie de configuracion pequena, real y verificable.

## Primary Actor(s)
- Confirmed: Desarrollo/mantenimiento del runtime.
- Inferred: Operaciones cuando necesita ajustar comportamiento sin tocar codigo.

## Stakeholders
- Desarrollo
- Operaciones
- Responsable de la documentacion tecnica

## Trigger
- Confirmed: Se detecta un setting documentado o expuesto en `Settings` que no tiene efecto real en la ejecucion.

## Main Flow
1. Inventariar los settings publicos del runtime.
2. Verificar para cada uno si gobierna comportamiento real, si es redundante o si esta obsoleto.
3. Hacer que los settings soportados controlen el runtime de verdad.
4. Eliminar o deprecar de forma explicita los knobs que no deban existir.

## Alternative Flows / Edge Cases
- Confirmed: Un setting puede salir del contrato soportado si resulta redundante con otro mas preciso.
- Inferred: Si algun knob debe mantenerse por compatibilidad, la compatibilidad debe quedar explicitada y no dejar un alias silencioso sin semantica clara.

## Business Rules
- Confirmed: La configuracion soportada debe ser una fuente de verdad del runtime, no solo un inventario de intenciones.
- Confirmed: No deben quedar constantes de negocio configurables hardcodeadas cuando el proyecto ya expone un setting para ese mismo concepto.
- Confirmed: Este change no redefine producto; cierra el contrato entre configuracion y ejecucion.

## Permissions / Visibility
- Confirmed: Cambio interno de configuracion/runtime.
- Pending: Ninguno.

## Scope In
- Confirmed: `review_window_days` frente al hardcode de 7 dias.
- Confirmed: `max_daily_opportunities` frente a su falta de uso runtime.
- Confirmed: Alineacion entre `Settings`, codigo runtime y documentacion tecnica que describe knobs operativos.

## Scope Out
- Confirmed: Contrato Docker/cron/volumen como tema operacional de despliegue.
- Confirmed: Limpieza amplia de documentacion historica.
- Confirmed: CI.

## Acceptance Criteria
- [ ] Cada setting soportado del runtime tiene efecto real comprobable o queda removido/deprecado explicitamente.
- [ ] No queda ninguna constante de negocio configurable hardcodeada donde ya exista un setting equivalente soportado.
- [ ] La documentacion tecnica de settings refleja solo knobs reales y vigentes.
- [ ] La superficie de configuracion resultante queda mas simple, no mas ambigua.

## Non-Functional Notes
- Confirmed: Debe reducir deuda de configuracion y falsos knobs.
- Inferred: La simplicidad del contrato de settings importa mas que el numero de parametros expuestos.

## Assumptions
- Confirmed: Hay evidencia suficiente en repo para tratar esto como un change propio.
- Confirmed: `runtime-documented-truth-alignment` debe ocurrir antes para no atar settings a una verdad funcional todavia discutida.

## Open Decisions
- Cerrar si `max_daily_opportunities` se elimina o se redefine con semantica distinta de `max_daily_deliveries`.
- Cerrar si algun alias temporal de compatibilidad merece existir o solo complica el contrato.

## Risks
- Confirmed: Intentar conservar todos los knobs historicos por "si acaso" perpetua la ambiguedad.
- Inferred: Cambiar semantica de settings sin simplificar documentacion puede empeorar la confusion en vez de resolverla.

## Readiness for SDD
Status: ready-for-sdd
Reason: El change tiene problema concreto, pruebas de repo suficientes, alcance acotado y criterios de aceptacion claros; las decisiones abiertas son de modelado del contrato final, no de descubrimiento adicional del outcome.
