# Product Discovery Brief: telegram-smoke-tests

## Classification
- Confirmado: El trabajo se clasifica como `single-change` porque resuelve un único objetivo de verificación: smoke test condicional de `send_message()` contra la API real de Telegram, sin añadir funcionalidad de producto.
- Inferido: Este cambio extiende el patrón de smoke tests env-gated ya establecido por `operational-integration-tests` (Reddit smoke), aplicándolo al canal de delivery (Telegram).
- Pendiente: Ninguno.

## Problem Statement
- Confirmado: Los 269 tests existentes mockean `httpx.post` en `test_telegram.py` — ninguno verifica que el bot token y chat_id reales produzcan una entrega exitosa en Telegram.
- Confirmado: `operational-integration-tests` ya tiene un smoke test para Reddit (`TestRedditSmokeOptional`) con el patrón env-gated, pero no cubre Telegram delivery.
- Inferido: Un token expirado, un chat_id invocado, o un cambio en la API de Telegram pasarían desapercibidos hasta un intento de delivery real en producción. Estos smoke tests proporcionan una verificación manual controlada.

## Goal / Desired Outcome
- Confirmado: Verificar, bajo demanda del desarrollador, que `send_message()` envía un mensaje de prueba exitosamente a un bot/chat de Telegram controlado (NO producción).
- Confirmado: Los smoke tests deben estar env-gated con `TELEGRAM_SMOKE_BOT_TOKEN` y `TELEGRAM_SMOKE_CHAT_ID` (credenciales dedicadas de prueba), no con las credenciales de producción.
- Confirmado: Los tests NO deben correr por defecto en CI — solo cuando las variables de entorno están explícitamente configuradas.

## Primary Actor(s)
- Confirmado: Desarrollador que necesita verificar la conectividad Telegram antes de un deploy o tras un cambio en la integración.
- Inferido: Pipeline de verificación manual pre-deploy.

## Stakeholders
- Desarrollo: necesita confirmación de que el canal de delivery funciona con credenciales reales.
- Operaciones: necesita smoke tests idempotentes que no contaminen el chat de producción.

## Trigger
- Confirmado: Ejecución manual con variables de entorno seteadas: `TELEGRAM_SMOKE_BOT_TOKEN=... TELEGRAM_SMOKE_CHAT_ID=... uv run pytest tests/ -x --tb=short`
- Confirmado: Sin las variables, el test se skipea automáticamente — no impacta CI.

## Main Flow

### Smoke 1: send_message() éxito real (S1)
1. Configurar `TELEGRAM_SMOKE_BOT_TOKEN` y `TELEGRAM_SMOKE_CHAT_ID` en el entorno.
2. Ejecutar `send_message()` con un mensaje de prueba HTML (identificable como smoke test, ej: "🧪 auto-reddit smoke test").
3. Verificar que retorna `True` (status 200 + ok=true).

### Smoke 2: send_message() con token inválido (S2)
1. Ejecutar `send_message()` con un token deliberadamente inválido.
2. Verificar que retorna `False` (manejo graceful de auth failure real).

### Smoke 3: mensaje HTML con formato real (S3)
1. Ejecutar `send_message()` con HTML válido (bold, link, monospace).
2. Verificar entrega exitosa — confirma que `parse_mode=HTML` funciona contra la API real.

## Alternative Flows / Edge Cases
- Confirmado: Si las variables de entorno no están seteadas, todos los smoke tests se saltan con `pytest.mark.skipif`.
- Confirmado: El chat de destino debe ser un canal/grupo de PRUEBAS, NO el chat de producción — el mensaje de smoke es identificable.
- Inferido: Si el bot no es miembro del chat de prueba, `send_message()` retornará `False` — esto se captura como fallo del smoke test.
- Confirmado: El smoke test de token inválido (S2) NO requiere variables de entorno — siempre puede correr, ya que usa un token dummy.

## Business Rules
- Confirmado: Los smoke tests son condicionales y no-bloqueantes — su fallo o ausencia NO impide que la suite principal pase.
- Confirmado: Credenciales de smoke son SEPARADAS de producción (`TELEGRAM_SMOKE_*`, no `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`).
- Confirmado: Los mensajes de smoke deben ser identificables (prefijo "🧪 smoke test") para distinguirlos de entregas reales.
- Inferido: La ubicación natural es `tests/test_integration/test_operational.py`, siguiendo el patrón existente de `TestRedditSmokeOptional`, en una clase `TestTelegramSmokeOptional`.
- Pendiente: Decidir si el smoke de token inválido (S2) vive en la misma clase o en `tests/test_delivery/test_telegram.py`.

## Permissions / Visibility
- Confirmado: Uso interno de desarrollo; no introduce interfaz ni cambios de comportamiento.
- Confirmado: Las credenciales de smoke no se documentan en `.env.example` — son opt-in explícito del desarrollador.

## Scope In
- Confirmado: Smoke test S1 — `send_message()` exitoso con bot/chat de prueba.
- Confirmado: Smoke test S2 — `send_message()` con token inválido retorna `False`.
- Confirmado: Smoke test S3 — envío HTML con formato real (bold, link, monospace).

## Scope Out
- Confirmado: Tests unitarios de `send_message()` — ya cubiertos por `test_telegram.py` (12 tests).
- Confirmado: Smoke test del pipeline completo `main.run()` contra Telegram real — demasiado amplio, requiere Reddit + DeepSeek reales.
- Confirmado: Modificación de `.env.example` para documentar credenciales de smoke.
- Confirmado: Cambios de funcionalidad en `send_message()` o cualquier módulo.

## Acceptance Criteria
- [ ] S1: `send_message()` con credenciales de smoke retorna `True` y el mensaje aparece en el chat de prueba.
- [ ] S2: `send_message()` con token inválido retorna `False` sin excepción no controlada.
- [ ] S3: `send_message()` con HTML formateado (bold, link, code) entrega exitosamente.
- [ ] Todos los smoke tests están env-gated con `pytest.mark.skipif` y se saltan sin las variables.
- [ ] Los 269+ tests existentes siguen pasando sin modificación.
- [ ] `uv run pytest tests/ -x --tb=short` sin variables de entorno pasa con los smoke tests skipeados.

## Non-Functional Notes
- Confirmado: Los tests deben ser idempotentes — re-ejecutar no causa efectos acumulativos.
- Confirmado: El mensaje de prueba debe ser identificable (emoji + "smoke test") para que el humano sepa que es artificial.
- Inferido: El smoke de token inválido (S2) no necesita variables de entorno — es un test siempre-disponible de graceful degradation.
- Pendiente: Definir si se incluye un sleep/retry para rate-limit de Telegram (unlikely para 3 mensajes).

## Assumptions
- Confirmado: El desarrollador que ejecuta los smoke tests tiene acceso a un bot de Telegram de pruebas y un chat/grupo donde el bot es miembro.
- Confirmado: El patrón env-gated de `TestRedditSmokeOptional` es el correcto a seguir — verificado en `test_operational.py:801-835`.
- Inferido: Las variables `TELEGRAM_SMOKE_BOT_TOKEN` y `TELEGRAM_SMOKE_CHAT_ID` son las correctas (nombradas con prefijo `SMOKE_` para distinguir de producción).
- Pendiente: Ninguno.

## Open Decisions
- Cerrado: Ubicación de los smoke tests — `tests/test_integration/test_operational.py`, clase `TestTelegramSmokeOptional`, siguiendo el patrón de `TestRedditSmokeOptional`.
- Cerrado: Variables de entorno — `TELEGRAM_SMOKE_BOT_TOKEN` y `TELEGRAM_SMOKE_CHAT_ID`, leídas con `os.getenv()`, NO via `Settings`.
- Cerrado: Smoke de token inválido — vive en la misma clase, usa token dummy hardcodeado, NO requiere env vars.
- Cerrado: `.env.example` no se modifica — credenciales de smoke son opt-in del desarrollador.

## Risks
- Confirmado: Si alguien configura las variables de smoke con credenciales de producción, los mensajes de prueba llegarán al chat real. Mitigación: nombre explícito `SMOKE_` + mensaje identificable como "🧪 smoke test".
- Inferido: Rate-limit de Telegram (30 msg/segundo) no aplica para 3 smoke tests secuenciales.
- Pendiente: Ninguno.

## Readiness for SDD
Status: **ready-for-sdd**

Reason: El cambio tiene un objetivo acotado (3 smoke tests env-gated), el patrón de implementación está verificado en el repo (`TestRedditSmokeOptional`), las dependencias son mínimas (solo `send_message()` de `telegram.py`), y los scope in/out están cerrados. No hay decisiones abiertas que bloqueen spec/diseño.
