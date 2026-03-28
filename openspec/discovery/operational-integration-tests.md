# Product Discovery Brief: operational-integration-tests

## Classification
- Confirmado: El trabajo se clasifica como `single-change` porque resuelve un único objetivo de verificación: pruebas operacionales de integración entre los módulos existentes del pipeline `main.run()`, sin añadir funcionalidad de producto.
- Inferido: Este cambio es el consumidor natural de los 5 changes archivados (reddit-candidate-collection, candidate-memory-and-uniqueness, thread-context-extraction, ai-opportunity-evaluation, telegram-daily-delivery) y verifica su orquestación conjunta.
- Pendiente: Ninguno.

## Problem Statement
- Confirmado: Los 259 tests existentes son unitarios con mocks y ninguno prueba el flujo orquestado de `main.run()` a nivel operacional. Existen gaps recurrentes documentados en verify-reports: (1) la reutilización de retries sin re-evaluación IA no tiene prueba de ejecución, (2) el paso de delivery no demuestra runtime que no re-entre en Reddit/AI/publicación, (3) la evaluación IA no prueba que no dispare side effects de otros límites.
- Inferido: Sin estas pruebas operacionales, los verify-reports de los changes 4 y 5 quedan con warnings que podrían esconder regresiones en integración real, especialmente en el flujo de retry sin re-evaluación IA que es la premisa clave de `candidate-memory`.
- Pendiente: Ninguno.

## Goal / Desired Outcome
- Confirmado: Probar con ejecución real (sin mock de orquestación) que `main.run()` conecta los módulos correctamente, que los retries reutilizan datos persistidos sin re-evaluar IA, que el delivery no dispara side effects de Reddit/AI, y que la evaluación no toca Reddit/delivery.
- Inferido: Las pruebas deben usar `mock.patch` sobre las dependencias externas (Reddit APIs, DeepSeek, Telegram HTTP) mientras mantienen la orquestación real y persistencia SQLite real con `tmp_path`.
- Pendiente: Definir si el cambio incluye marcadores pytest para smoke tests condicionales (ver Scope Out).

## Primary Actor(s)
- Confirmado: Pipeline diario `main.run()` como unidad bajo prueba.
- Inferido: El equipo de desarrollo que necesita confianza operacional antes de cambios futuros al pipeline.

## Stakeholders
- Desarrollo: necesita fe en que la orquestación no introduce regresiones silenciosas.
- Operaciones: necesita que la verificación automatizada detecte roturas de límites entre módulos.

## Trigger
- Confirmado: Ejecución de `uv run pytest tests/ -x --tb=short` como parte del ciclo de verificación post-cambios archivados.
- Inferido: Los verify-reports de changes 4 y 5 recomendaron explícitamente estas pruebas (SUGGESTION en telegram-daily-delivery y ai-opportunity-evaluation).

## Main Flow

### Prioridad 1: Retry-reuse sin re-evaluación IA (P1 — crítico)
1. Persistir en SQLite real un registro `pending_delivery` con `opportunity_data` válido.
2. Ejecutar `main.run()` con `evaluate_batch` parcheado para que falle si es invocado.
3. Verificar que `deliver_daily` lee el `opportunity_data` persistido y envía el mensaje sin llamar a `evaluate_batch`.
4. Verificar que `mark_sent` se ejecuta tras envío exitoso.

### Prioridad 2: Delivery no re-entra en Reddit/AI/publishing (P2)
1. Ejecutar `main.run()` con `collect_candidates`, `fetch_thread_contexts` y `evaluate_batch` parcheados para alimentar datos controlados.
2. Parchear `send_message` y `evaluate_batch` como centinelas: si son llamados durante delivery, el test falla.
3. Verificar que `deliver_daily` opera solo sobre `get_pending_deliveries()` sin tocar Reddit ni IA.

### Prioridad 3: Evaluación no dispara side effects de Reddit/delivery (P3)
1. Ejecutar `evaluate_batch` con `collect_candidates`, `fetch_thread_contexts` y `deliver_daily` parcheados como centinelas.
2. Verificar que la evaluación solo consume `ThreadContext` y no llama a Reddit ni delivery.

### Prioridad 4: Exclusión por memoria + corte diario (P4)
1. Ejecutar `main.run()` dos veces con SQLite real (`tmp_path`): la primera acepta/rechaza posts, la segunda debe excluir los decididos.
2. Verificar que `get_decided_post_ids()` excluye `sent` y `rejected` pero NO `pending_delivery`.

## Alternative Flows / Edge Cases
- Confirmado: Un post en `pending_delivery` NO debe excluirse de la revisión diaria (compite de nuevo) pero SÍ debe recibir retry en delivery sin re-evaluación IA — esto es el comportamiento diseñado en `candidate-memory`.
- Confirmado: Si `evaluate_batch` devuelve todos `None` (skip), el pipeline debe completar sin error y delivery debe procesar retries pendientes.
- Confirmado: Si `send_message` falla para una oportunidad, el registro permanece en `pending_delivery` y aparece en el siguiente ciclo de retry.
- Inferido: Los smoke tests contra Reddit real (si se incluyen) deben ser condicionales mediante `pytest.mark.skipif` con variable de entorno, no deben correr en CI por defecto.
- Pendiente: Ninguno.

## Business Rules
- Confirmado: El change se clasifica como `single-change` — no introduce funcionalidad, solo verificación operacional.
- Confirmado: `main.run()` se prueba con `mock.patch` sobre dependencias externas, sin refactorizar para inyección de dependencias.
- Confirmado: `CandidateStore` usa SQLite real con `tmp_path` para tests multi-run, no se mockea.
- Confirmado: La priorización de pruebas sigue: retry-reuse → delivery-boundary → evaluation-boundary → memory-exclusion.
- Confirmado: Smoke tests contra Reddit real son scope condicional/optional, no criterio de éxito del change.
- Inferido: Las pruebas operacionales NO reemplazan los 259 unit tests existentes; los complementan.
- Pendiente: Ninguno.

## Permissions / Visibility
- Confirmado: Uso interno de desarrollo; no introduce interfaz ni cambios de comportamiento.
- Pendiente: Ninguno.

## Scope In
- Confirmado: Prueba P1 — retry-reuse sin re-evaluación IA usando SQLite real y `mock.patch` sobre `evaluate_batch`.
- Confirmado: Prueba P2 — delivery no re-entra en Reddit/AI/publishing usando `mock.patch` como centinela.
- Confirmado: Prueba P3 — evaluación no dispara side effects de Reddit/delivery.
- Confirmado: Prueba P4 — exclusión por memoria con `sent`/`rejected` + corte diario, SQLite real multi-run.
- Confirmado: Smoke tests condicionales contra Reddit real (optional, con `pytest.mark.skipif`).

## Scope Out
- Confirmado: Refactorización de `main.run()` para inyección de dependencias.
- Confirmado: Cambios de funcionalidad en ningún módulo del pipeline.
- Confirmado: Nuevos tests unitarios para lógica interna de módulos (ya cubiertos por los 259 existentes).
- Confirmado: Cobertura de código (coverage) — fuera del alcance, `openspec/config.yaml` no lo configura.
- Confirmado: Cambios en `openspec/config.yaml` para añadir build_command o coverage_threshold.

## Acceptance Criteria
- [ ] P1: Un test ejecuta `main.run()` con un `pending_delivery` persistido y demuestra que `evaluate_batch` NO es invocado mientras el mensaje se envía correctamente.
- [ ] P2: Un test ejecuta `main.run()` y verifica que ni `collect_candidates`, `fetch_thread_contexts` ni `evaluate_batch` son llamados durante la fase de delivery.
- [ ] P3: Un test ejecuta `evaluate_batch` y verifica que ni `collect_candidates`, `fetch_thread_contexts` ni `deliver_daily` son invocados.
- [ ] P4: Dos ejecuciones consecutivas de `main.run()` con SQLite real demuestran que posts `sent`/`rejected` se excluyen y `pending_delivery` recibe retry.
- [ ] Todos los tests pasan con `uv run pytest tests/ -x --tb=short` sin romper los 259 tests existentes.
- [ ] (Opcional) Smoke tests contra Reddit real están implementados con `pytest.mark.skipif` y no corren por defecto.

## Non-Functional Notes
- Confirmado: Las pruebas deben ser deterministas — no dependen de tiempo real ni de servicios externos.
- Confirmado: El uso de `tmp_path` para SQLite asegura aislamiento entre tests.
- Inferido: Cada test de orquestación debe ser independiente y no depender del orden de ejecución.
- Pendiente: Ninguno.

## Assumptions
- Confirmado: Los 5 changes archivados entregan un pipeline funcional completo con 259 tests unitarios pasando.
- Confirmado: `mock.patch` es la estrategia correcta para parchear dependencias sin refactorizar `main.run()`.
- Confirmado: `tmp_path` de pytest proporciona aislamiento suficiente para SQLite multi-run.
- Inferido: La estructura de tests existente (`tests/test_delivery/`, `tests/test_evaluation/`, etc.) puede extenderse con un nuevo archivo `tests/test_integration/` o mantenerse en los módulos existentes.
- Pendiente: Decidir ubicación exacta del archivo de tests de integración operacional.

## Open Decisions
- Cerrado: Ubicación del archivo de tests — `tests/test_integration/test_operational.py` con `tests/test_integration/__init__.py`, siguiendo la convención del repo `tests/test_<area>/`.
- Cerrado: Variables de entorno para smoke tests — usar `REDDIT_SMOKE_API_KEY` leída directamente con `os.getenv()` en los tests, NO via `Settings`.
- Cerrado: Implementación de smoke tests — condicionales/no-bloqueantes usando `pytest.mark.skipif(not REDDIT_SMOKE_KEY, reason="...")`.
- Cerrado: `.env.example` no se modifica para esta variable de test-only.

## Risks
- Confirmado: Si `mock.patch` parchea el módulo incorrecto (ej. el import local en lugar del global), los centinelas no detectarán llamadas reales. Mitigación: usar `patch("auto_reddit.main.evaluate_batch")` en el namespace del caller.
- Confirmado: Si los tests dependen de `time.time()` real, serán no deterministas. Mitigación: parchear `time.time` o usar fechas fijas inyectadas donde sea posible.
- Inferido: La prueba P4 (multi-run) requiere que `main.run()` sea idempotente sobre la misma DB — esto es cierto por diseño de upserts en `CandidateStore`.

## Readiness for SDD
Status: **ready-for-sdd**

Reason: El change tiene cerrado problema, objetivo, clasificación, estrategia de testing confirmada (mock.patch + SQLite real + tmp_path), priorización P1→P4, criterios de aceptación verificables, y scope in/out definidos. Los puntos abiertos restantes (ubicación del archivo de tests, token para smoke tests) son decisiones de implementación que no bloquean la fase de spec/diseño. Los verify-reports de changes 4 y 5 documentan explícitamente las sugerencias que este change resuelve.
