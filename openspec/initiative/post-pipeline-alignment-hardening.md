# Initiative: post-pipeline-alignment-hardening

## Status
active

## Vision
Cerrar la brecha entre el pipeline ya archivado y su realidad operativa actual, dejando runtime, configuracion, ejecucion operacional, CI y documentacion alineados con una unica verdad mantenible.

## Desired Outcomes
- El runtime ejecuta lo que la documentacion vigente dice que debe ejecutar.
- La ejecucion con entorno persistente queda definida y endurecida con un contrato operativo claro.
- Existe una base minima de CI que verifique el proyecto sin depender de credenciales reales.
- Los settings soportados gobiernan de verdad el comportamiento runtime; los knobs huerfanos desaparecen.
- La logica y artefactos medio aterrizados se conectan o se eliminan para reducir ambiguedad.
- La documentacion queda reordenada por verdad vigente, historico y planning.

## Scope Notes
- Se trata como iniciativa porque combina runtime, configuracion, despliegue/operacion, calidad y arquitectura de informacion; forzarlo en un unico change mezclaria resultados semindependientes.
- Se respeta la preferencia del usuario de mantener cada prioridad como un change separado salvo evidencia clara en contra.
- No se reabre el pipeline funcional archivado; se trabaja sobre alineacion, endurecimiento y mantenibilidad post-pipeline.

## Domain Context
- El pipeline principal esta archivado y funcional.
- La verdad documental vigente sigue siendo `docs/product/product.md`, `docs/integrations/reddit/api-strategy.md` y `docs/architecture.md`.
- Existen restos historicos y de transicion en `TFM/`, `openspec/discovery/` y comentarios de codigo.

## Candidate Changes

### 1. runtime-documented-truth-alignment
Status: proposed
Goal: Alinear el comportamiento runtime con la verdad documental vigente en los puntos donde hoy existe divergencia observable.
Dependencies: none
Why separate: Fija la linea base funcional antes de endurecer ejecucion, CI o configuracion.

### 2. environment-persistence-execution-hardening
Status: proposed
Goal: Definir y endurecer exactamente como debe ejecutarse el sistema con `.env`, volumen persistente SQLite y planificacion externa.
Dependencies: runtime-documented-truth-alignment
Why separate: Es un outcome operacional/deployment distinto del comportamiento de negocio del runtime.

### 3. minimum-ci-baseline
Status: proposed
Goal: Introducir una base minima de CI que valide el proyecto con `uv` y la suite segura por defecto.
Dependencies: runtime-documented-truth-alignment
Why separate: CI es una capacidad transversal de verificacion, no un ajuste del runtime ni del despliegue.

### 4. settings-govern-runtime
Status: proposed
Goal: Garantizar que los settings soportados gobiernan el runtime real y que no queden parametros documentados pero ignorados.
Dependencies: runtime-documented-truth-alignment
Why separate: Es un cierre de contrato de configuracion, diferente de despliegue, CI o limpieza documental.

### 5. connect-or-remove-half-landed-logic
Status: proposed
Goal: Resolver conceptos y artefactos runtime-adjacent que quedaron a medio aterrizar y hoy generan ruido o superficie falsa.
Dependencies: settings-govern-runtime
Why separate: Conviene hacerlo despues de cerrar la autoridad del runtime/config para no borrar o consolidar en falso.

### 6. docs-information-architecture-cleanup
Status: proposed
Goal: Reordenar la documentacion para que la verdad vigente, el historico y el planning queden claramente separados y navegables.
Dependencies: runtime-documented-truth-alignment, environment-persistence-execution-hardening, minimum-ci-baseline, settings-govern-runtime, connect-or-remove-half-landed-logic
Why separate: Es una capa de informacion y mantenibilidad; debe consolidar las decisiones cerradas por los changes previos.

## Dependency Notes
- `runtime-documented-truth-alignment` va primero porque define que comportamiento es canonicamente correcto.
- `environment-persistence-execution-hardening`, `minimum-ci-baseline` y `settings-govern-runtime` pueden planearse despues de 1, pero se mantienen en el orden pedido por el usuario.
- `connect-or-remove-half-landed-logic` debe venir despues de `settings-govern-runtime` para distinguir entre knobs validos y restos que sobran.
- `docs-information-architecture-cleanup` cierra la iniciativa para no limpiar documentacion sobre una base todavia moviendose.

## Current Recommendation
Next recommended change: runtime-documented-truth-alignment

## Decisions Log
- Se clasifica la peticion como `initiative`, no como `single-change`, porque contiene seis outcomes semindependientes.
- Se mantiene un change por prioridad solicitada; no hay evidencia suficiente para colapsar ninguna en este momento.
- Se evita crear proposal/spec/design/tasks en esta fase; solo iniciativa + discovery listos para SDD.
