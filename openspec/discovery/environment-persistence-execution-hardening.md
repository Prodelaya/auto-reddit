# Product Discovery Brief: environment-persistence-execution-hardening

## Problem Statement
- Confirmed: La arquitectura y el README documentan un modelo de contenedor efimero con cron externo y SQLite en volumen Docker (`README.md:27-35`, `docs/architecture.md:31-38`), pero la configuracion actual no deja ese contrato cerrado de forma inequívoca.
- Confirmed: `docker-compose.yml` monta un volumen en `/data`, mientras `src/auto_reddit/config/settings.py` deja `db_path="auto_reddit.db"` por defecto y `Dockerfile` fija `WORKDIR /app`; asi, la persistencia documentada en volumen no queda garantizada por configuracion.
- Confirmed: El repo usa varias variables de entorno operativas y de smoke, pero no existe un artefacto unico que deje claro que es obligatorio, que es opcional, que es productivo y que es solo para tests live.
- Inferred: Sin ese contrato, es facil ejecutar el contenedor de forma aparentemente correcta pero perder persistencia o mezclar credenciales/entornos.

## Goal / Desired Outcome
- Confirmed: Dejar especificado y endurecido exactamente como debe ejecutarse el sistema con `.env`, volumen persistente SQLite y planificacion externa.
- Confirmed: El resultado debe convertir la ejecucion en un contrato operativo claro y reproducible, no en una interpretacion dispersa entre README, arquitectura y compose.
- Inferred: La salida esperada incluye una frontera nitida entre configuracion obligatoria de runtime y variables opcionales de smoke/manual.

## Primary Actor(s)
- Confirmed: Operaciones / mantenedor que despliega y ejecuta el contenedor.
- Inferred: Desarrollo cuando necesita reproducir localmente la forma correcta de ejecucion persistente.

## Stakeholders
- Operaciones
- Desarrollo
- Responsable del producto que necesita confianza en idempotencia y persistencia

## Trigger
- Confirmed: Se necesita ejecutar el sistema en su modo documentado de contenedor efimero con persistencia real entre runs.

## Main Flow
1. Identificar el contrato operativo vigente para `.env`, volumen SQLite y cron externo.
2. Cerrar las ambiguedades entre configuracion runtime, Docker y documentacion.
3. Definir que debe configurarse, que debe endurecerse y que queda explicitamente fuera.
4. Dejar el change listo para que una implementacion futura materialice ese contrato sin reinterpretaciones.

## Alternative Flows / Edge Cases
- Confirmed: La ejecucion local de desarrollo puede seguir existiendo, pero no debe confundirse con la ejecucion persistente de produccion/VPS.
- Confirmed: Las variables de smoke (`REDDIT_SMOKE_*`, `TELEGRAM_SMOKE_*`) deben permanecer separadas de las credenciales operativas normales.
- Inferred: Si el repositorio decide no sostener `docker-compose.yml` como referencia primaria, el change debe declararlo y mover la verdad operativa a un artefacto mas apropiado.

## Business Rules
- Confirmed: El sistema no ejecuta como daemon persistente; el modelo es run-and-exit.
- Confirmed: SQLite debe sobrevivir entre ejecuciones cuando se use el modo desplegado documentado.
- Confirmed: El cambio define configuracion/hardening alrededor de la ejecucion; no reabre logica de negocio del pipeline.
- Inferred: Debe quedar claro que secretos reales no se versionan y que `.env.example` es contrato publico, no entorno activo.

## Permissions / Visibility
- Confirmed: Cambio interno de operacion/despliegue.
- Pending: Ninguno.

## Scope In
- Confirmed: Contrato de `db_path` persistente respecto al volumen Docker documentado.
- Confirmed: Contrato de variables de entorno obligatorias vs opcionales vs smoke-only.
- Confirmed: Relacion entre contenedor efimero, cron externo y modo de ejecucion esperado.
- Inferred: Criterios minimos de hardening para evitar ejecuciones aparentemente validas pero operativamente inseguras o efimeras.

## Scope Out
- Confirmed: Cambios en la logica del pipeline funcional.
- Confirmed: CI.
- Confirmed: Reordenacion amplia de documentacion fuera del contrato operativo necesario.

## Acceptance Criteria
- [ ] Existe una definicion unica de como debe persistirse SQLite en el modo de ejecucion documentado.
- [ ] Queda explicitado que variables son obligatorias para runtime normal, cuales son opcionales y cuales son exclusivas de smoke/live tests.
- [ ] Queda explicitado como debe invocarse el proceso diario en el modelo de cron externo + contenedor efimero.
- [ ] Se eliminan ambiguedades operativas entre `Dockerfile`, `docker-compose.yml`, `Settings` y documentacion vigente.

## Non-Functional Notes
- Confirmed: El objetivo principal es reducir riesgo operativo y perdida silenciosa de persistencia.
- Inferred: La solucion futura debe ser reproducible localmente y en VPS sin interpretaciones manuales ocultas.

## Assumptions
- Confirmed: El modelo operativo documentado (contenedor efimero + cron externo + SQLite persistente) sigue siendo el correcto.
- Confirmed: La brecha actual entre `/data` y `db_path` es evidencia suficiente para justificar un change propio.

## Open Decisions
- Cerrar que artefacto sera la referencia operativa primaria: `README.md`, `docs/architecture.md`, documento operacional dedicado o combinacion minima.
- Cerrar si `docker-compose.yml` sigue siendo el entrypoint recomendado o solo una referencia de ejemplo.

## Risks
- Confirmed: Si este contrato no se cierra, el sistema puede parecer persistente mientras escribe la base fuera del volumen previsto.
- Inferred: Mezclar credenciales de smoke y runtime real puede causar falsos positivos o envios al destino equivocado.

## Readiness for SDD
Status: ready-for-sdd
Reason: El problema, actor, outcome, alcance y criterios de aceptacion estan suficientemente cerrados; las decisiones abiertas restantes son de encaje documental/operativo y no cambian el resultado funcional del change.
