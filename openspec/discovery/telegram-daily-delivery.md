# Discovery: Telegram Daily Delivery

## Change Boundaries

Single change: `telegram-daily-delivery`.

Entrega diaria determinista de oportunidades aceptadas por Telegram. Sin evaluación AI, sin editorial backlog, sin publicación autónoma en Reddit dentro de este cambio.

## Scope

- Reutilizar evaluación estructurada persistida (`structured_evaluation`) en reintentos — **sin re-evaluar con AI**.
- Estado `sent` solo tras entrega exitosa en Telegram.
- Límite diario: **8 mensajes**.
- Prioridad: **reintentos primero**, luego nuevas oportunidades hasta completar los 8.
- Modo de parseo: **HTML**.
- Resumen se envía primero; si falla, continúa con los mensajes de oportunidades.
- TTL de `pending_delivery`: L/M/X hasta el viernes; J/V hasta el siguiente lunes.

## Closed Decisions

| # | Decisión | Razón |
|---|----------|-------|
| 1 | Reintentos indefinidos mientras el registro sea operativamente válido | No perder oportunidades por transient failures |
| 2 | Reintentos tienen prioridad sobre nuevas entregas (dentro del cap de 8) | FIFO de oportunidades pendientes de re-envío |
| 3 | No re-evaluar con AI en reintentos | La evaluación ya está persistida; re-evaluar es costoso e innecesario |
| 4 | `sent` solo tras confirmación de Telegram | Integridad operativa — no marcar como enviado si Telegram falló |
| 5 | HTML como modo de parseo | Soporta negrita, links, monospace — suficiente para formato de oportunidades |
| 6 | Resumen primero pero no bloqueante | Si el resumen falla, las oportunidades individuales se envían igual |
| 7 | TTL semanal: Mon/Tue/Wed→Friday, Thu/Fue→next Monday | Evita acumulación infinita, da ventana razonable para reintentos |

## Dependencies

Depends on:
- `candidate-memory-and-uniqueness` — requiere persistencia de `pending_delivery` y `structured_evaluation` en SQLite.

Does NOT depend on:
- `ai-opportunity-evaluation` — la evaluación se consume como dato, no se ejecuta en este change.

## Readiness for SDD

Ready. Decisions are closed, scope is bounded, dependencies are clear.

## Verification Hooks

- Confirmar que `structured_evaluation` se reutiliza en reintentos sin llamada a DeepSeek.
- Confirmar que `sent` solo se marca tras HTTP 200 de Telegram Bot API.
- Confirmar que el cap de 8 diarios se respeta con reintentos primero.
- Confirmar comportamiento de TTL según regla semanal.
