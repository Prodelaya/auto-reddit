# Product Discovery Brief: settings-govern-runtime

> **REVISADO 2026-03-30** — Premisas originales corregidas tras verificación de código
> post-hardening (`runtime-documented-truth-alignment` + `environment-persistence-execution-hardening`).

---

## ~~Problem Statement~~ → Estado actual verificado

### Premisas originales — OBSOLETAS

Las siguientes afirmaciones del discovery brief original ya NO son verdad:

- ~~`review_window_days` no gobierna runtime (hardcode `_7_DAYS_SECONDS`)~~ → **FALSO**.
  `client.py:310` calcula `cutoff_utc = now_utc - (settings.review_window_days * 86400)`.
  El hardcode fue eliminado por `runtime-documented-truth-alignment`.
- ~~`max_daily_opportunities` no es consumido por el runtime~~ → **FALSO**.
  `delivery/__init__.py:81` pasa `cap=settings.max_daily_opportunities` al selector.

### Estado real del contrato de settings (verificado en código)

| Setting | ¿Gobierna runtime? | Consumidor real |
|---------|-------------------|----------------|
| `deepseek_api_key` | SÍ | `evaluation/evaluator.py` → api_key OpenAI client |
| `telegram_bot_token` | SÍ | `delivery/telegram.py` |
| `telegram_chat_id` | SÍ | `delivery/telegram.py` |
| `reddit_api_key` | SÍ | `reddit/client.py` → X-RapidAPI-Key |
| `max_daily_opportunities` | SÍ | `delivery/__init__.py:81` cap selector |
| `review_window_days` | SÍ | `reddit/client.py:310` cutoff_utc |
| `daily_review_limit` | SÍ | `main.py:64` recorta set antes de evaluación IA |
| `db_path` | SÍ | `persistence/store.py:20` |
| `deepseek_model` | SÍ | `evaluation/evaluator.py:331` |

**RESULTADO: TODOS los settings gobiernan runtime. No hay knobs decorativos ni sin consumidor.**

---

## Problem Statement (revisado)

El contrato de settings es funcionalmente correcto pero está documentado de forma incompleta
y ambigua. Los problemas reales que quedan son de alineación documental/semántica:

1. `daily_review_limit` no está documentado con precisión en `docs/architecture.md` §6:
   no queda explícito que recorta el set de candidatos **antes** de la evaluación IA
   (a diferencia de `max_daily_opportunities`, que recorta el set de entrega Telegram
   **después** de la evaluación).

2. `deepseek_model` y `db_path` no aparecen en la sección de knobs configurables de
   `docs/architecture.md`. Son parámetros operativos/infraestructura, no secretos,
   pero ningún documento los clasifica explícitamente como tales.

3. `docs/product/product.md` solo menciona `review_window_days` y `max_daily_opportunities`;
   omite `daily_review_limit`, que también controla el comportamiento observable del producto.

4. `.env.example` documenta `DB_PATH=/data/auto_reddit.db` (valor Docker correcto) sin nota
   del valor por defecto real en `Settings` (`"auto_reddit.db"`), lo que puede confundir
   en desarrollo local.

---

## Goal / Desired Outcome

Conseguir que la **superficie documentada** de settings coincida exactamente con el contrato
runtime real, con semántica clara para cada knob y sin ambigüedad sobre cuándo y dónde aplica.

---

## Primary Actor(s)

- Desarrollo/mantenimiento del runtime.
- Operaciones cuando necesita ajustar comportamiento sin tocar código.

## Stakeholders

- Desarrollo
- Operaciones
- Responsable de la documentación técnica

---

## Trigger

Verificación post-hardening detecta que la documentación de settings no refleja el estado
real del código: knobs que ya existen y gobiernan runtime no están documentados con semántica
precisa.

---

## Main Flow

1. Actualizar `docs/architecture.md` §6 con semántica precisa de `daily_review_limit`.
2. Documentar `deepseek_model` y `db_path` como configurables operativos (no secretos).
3. Actualizar `docs/product/product.md` para incluir `daily_review_limit`.
4. Revisar `.env.example` para reflejar coherencia entre valor comentado y default real.

---

## Scope In

- `docs/architecture.md` — sección §6 Parámetros configurables (semántica de todos los knobs).
- `docs/product/product.md` — añadir `daily_review_limit`.
- `.env.example` — nota de coherencia sobre `DB_PATH`.
- Ningún cambio de código en el runtime (el contrato funcional ya es correcto).

## Scope Out

- No eliminar ningún setting (todos tienen efecto real).
- No conectar ni remover lógica half-landed (eso es `connect-or-remove-half-landed-logic`).
- No cambiar contrato Docker/cron/volumen.
- No ampliar CI.
- No limpiar documentación histórica más allá de la sección de configuración.

---

## Acceptance Criteria

- [ ] `docs/architecture.md` §6 describe con semántica precisa todos los knobs de `Settings`,
      distinguiendo explícitamente `daily_review_limit` (recorte pre-evaluación IA) de
      `max_daily_opportunities` (cap de entrega Telegram).
- [ ] `deepseek_model` y `db_path` están clasificados como parámetros operativos/infraestructura
      en la documentación de configuración.
- [ ] `docs/product/product.md` menciona `daily_review_limit` con su semántica correcta.
- [ ] `.env.example` tiene nota de coherencia para `DB_PATH` respecto al default real.
- [ ] Ninguna sección de documentación describe un setting como "sin efecto" o "decorativo".

---

## Non-Functional Notes

- Cambio principalmente documental — riesgo bajo.
- La claridad semántica entre `daily_review_limit` y `max_daily_opportunities` (ambos con
  default 8) es el punto más crítico para evitar confusión operativa futura.

---

## Assumptions

- El contrato funcional de `settings.py` es correcto y no requiere modificación.
- `runtime-documented-truth-alignment` y `environment-persistence-execution-hardening` ya
  están archivados y el código verificado refleja su estado post-merge.

---

## Open Decisions

- Ninguna decisión de modelado pendiente. El contrato funcional está cerrado.
- Decisión editorial menor: si `deepseek_model` y `db_path` merecen subsección propia en
  `docs/architecture.md` o se integran en la tabla existente.

---

## Risks

- BAJO: Alcance muy acotado; solo documentación y `.env.example`.
- BAJO: `daily_review_limit` y `max_daily_opportunities` tienen el mismo valor por defecto (8).
  Si no se distingue explícitamente su punto de aplicación en el pipeline, la confusión persiste
  a pesar del cambio documental.

---

## Readiness for SDD

Status: ready-for-sdd
Reason: El alcance real está verificado en código, los problemas son concretos y acotados,
y los criterios de aceptación son verificables sin ambigüedad. No se requiere exploración adicional.
