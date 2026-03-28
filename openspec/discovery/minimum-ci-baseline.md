# Product Discovery Brief: minimum-ci-baseline

## Problem Statement
- Confirmed: El repositorio no tiene `.github/workflows/` y por tanto carece de una base minima de CI versionada.
- Confirmed: El proyecto ya tiene una interfaz de verificacion clara (`uv sync`, `uv run pytest tests/ -x --tb=short`) y smoke tests env-gated que no deben bloquear ejecuciones normales.
- Inferred: Sin CI minima, una regresion puede entrar aunque la suite local y las convenciones del repo ya esten listas para automatizarse.

## Goal / Desired Outcome
- Confirmed: Crear una base minima de CI que valide el proyecto con `uv` y la suite segura por defecto.
- Confirmed: El change debe cubrir lo minimo necesario para dar feedback automatico sobre integridad basica del repo, no construir una plataforma CI compleja.
- Inferred: El baseline debe respetar que los smoke tests reales son opcionales y env-gated.

## Primary Actor(s)
- Confirmed: Equipo de desarrollo.
- Inferred: Mantenedor del repo que necesita una señal automatica minima en PR/push.

## Stakeholders
- Desarrollo
- Mantenimiento del repositorio

## Trigger
- Confirmed: Cada push o pull request donde se quiera validar el estado basico del proyecto sin depender de credenciales reales.

## Main Flow
1. Preparar el entorno CI con la version de Python soportada por el repo y `uv`.
2. Instalar dependencias del proyecto siguiendo la interfaz oficial del repositorio.
3. Ejecutar la suite de verificacion segura por defecto.
4. Publicar el resultado como baseline automatizado del repositorio.

## Alternative Flows / Edge Cases
- Confirmed: Los smoke tests live pueden quedar skipped por defecto y no deben convertir la CI minima en un pipeline dependiente de secretos externos.
- Inferred: Si una comprobacion adicional muy barata y estable (por ejemplo, import/package smoke) ya viene incluida en la suite normal, no necesita job separado.

## Business Rules
- Confirmed: `uv` es la unica interfaz soportada para instalar y ejecutar.
- Confirmed: La CI minima no debe requerir secretos de produccion ni de smoke.
- Confirmed: El objetivo es baseline minima; matrices amplias, coverage avanzada o despliegue automatico quedan fuera.

## Permissions / Visibility
- Confirmed: Senal interna de calidad del repositorio.
- Pending: Ninguno.

## Scope In
- Confirmed: Workflow minimo versionado en el repo.
- Confirmed: Preparacion de Python compatible con `requires-python >=3.14`.
- Confirmed: Ejecucion automatizada de la suite segura por defecto con `uv`.
- Inferred: Manejo explicito del comportamiento expected/skipped de smoke tests.

## Scope Out
- Confirmed: Deploy.
- Confirmed: Smoke tests live obligatorios.
- Confirmed: Coverage gates, matrices multi-version, linting no estandarizado o release automation.

## Acceptance Criteria
- [ ] Existe una CI minima versionada en el repo.
- [ ] La CI usa `uv` para instalar y ejecutar la verificacion.
- [ ] La CI valida el proyecto sin requerir secretos reales.
- [ ] El comportamiento de los smoke tests opcionales queda alineado con el baseline normal de CI.

## Non-Functional Notes
- Confirmed: Debe ser rapida, mantenible y de bajo coste operacional.
- Inferred: Cuanto menor sea la complejidad inicial, mas probable es que se mantenga estable.

## Assumptions
- Confirmed: La ausencia total de workflows justifica un change propio.
- Confirmed: La suite actual es suficientemente util como primer baseline.

## Open Decisions
- Cerrar si el baseline corre solo en PR/push o tambien en otras señales basicas.
- Cerrar si conviene separar job unico o varios pasos dentro de un unico workflow minimo.

## Risks
- Confirmed: Si se intenta meter demasiado alcance, el change dejara de ser "minimum CI".
- Inferred: Si no se documenta que los smoke son opcionales, puede aparecer confusion sobre skips esperados.

## Readiness for SDD
Status: ready-for-sdd
Reason: El change tiene outcome unico, trigger claro, fronteras bien acotadas y criterios de aceptacion verificables sin requerir mas descubrimiento funcional.
