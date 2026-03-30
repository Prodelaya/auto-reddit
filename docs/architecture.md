# Decisiones Arquitectonicas Fundacionales

Fuente de verdad de arquitectura del proyecto auto-reddit.
Para decisiones de producto, ver `docs/product/product.md`.

---

## 1. Stack principal

- **Lenguaje**: Python 3.14
- **Gestor de dependencias**: uv
- **Despliegue**: Docker en VPS

## 2. Estructura del codigo

Monolito modular con contratos explicitos (Opcion D).

```
src/auto_reddit/
├── reddit/          # extraccion de candidatos y contexto
├── evaluation/      # evaluacion IA con DeepSeek
├── delivery/        # entrega por Telegram
├── persistence/     # memoria operativa SQLite
├── shared/          # contratos Pydantic compartidos
├── config/          # settings con pydantic-settings
└── main.py          # orquestador del proceso diario
```

## 3. Modelo operativo

- **Contenedor efimero + cron externo** en el VPS.
- El contenedor arranca, ejecuta el proceso diario completo y muere.
- No hay proceso persistente corriendo 24/7.

## 4. Persistencia minima

- **Motor**: SQLite (fichero en volumen Docker).
- **Modelo operativo minimo** por post:
  - `sent`: ya enviado a Telegram. No se reenvia ni vuelve a competir.
  - `rejected`: rechazo final de negocio por la IA; no aplicar respuesta, post cerrado o sin valor de intervencion. No vuelve a competir ni a reevaluarse.
- **Sin backlog explicito**: no existe estado `approved` ni cola editorial persistente.
- **Regla de ventana**: si un post no se selecciona hoy pero sigue dentro de la ventana de 7 dias y no esta marcado como `sent` ni como `rejected`, manana vuelve a competir normalmente desde la ventana temporal.
- **No-estado explicito**: `not selected today` no se persiste como estado final.
- **Idempotencia de entrega**: si Telegram falla despues de una aceptacion de IA, se reintenta el envio sin reevaluar la IA.
- **Clave**: `post_id` nativo de Reddit (ej: `1s49yam`).
- **TTL**: fecha de creacion del post + 7 dias. Se purgan al inicio de cada ejecucion.
- **Esquema minimo**: `post_id | status | created_at`

## 5. Contratos internos

- Pydantic para todos los contratos entre modulos.
- Definidos en `shared/contracts.py`.
- Ningun modulo importa a otro modulo directamente.
- Los modulos solo importan de `shared/` y de `config/`.
- `main.py` es el unico que conoce a todos los modulos y los conecta.

## 6. Configuracion y secretos

- **pydantic-settings** con `.env`.
- **Validacion al arrancar**: si falta una variable, el proceso no empieza.
- **Variables necesarias**: `DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `REDDIT_API_KEY` (se mantiene este nombre por compatibilidad, pero representa la API key de RapidAPI compartida para las APIs de Reddit consumidas por el proyecto).
- **Parametros de producto configurables**:
  - `max_daily_opportunities`: 8 _(cap post-evaluación IA: máximo de oportunidades entregadas tras evaluación y selección (`delivery/__init__.py:81`))_
  - `review_window_days`: 7 _(fuente de verdad que gobierna la ventana temporal en coleccion)_
  - `daily_review_limit`: 8 _(cap pre-evaluación IA: máximo de posts que entran a revisión diaria (`main.py:64`))_
  - `deepseek_model`: `deepseek-chat` _(modelo DeepSeek utilizado en la evaluación (`evaluator.py:331`))_
  - `db_path`: `auto_reddit.db` _(ruta del fichero SQLite de memoria operativa (`store.py:20`))_

## 7. Logging y trazabilidad

- Solo **stdout** (se captura con `docker logs`).
- Nivel minimo util: contadores de decisiones + errores.
- Ejemplo de salida esperada:
  - Proceso iniciado
  - X candidatos encontrados
  - X ya enviados, descartados
  - X enviados a evaluacion IA
  - X validos, X descartados
  - X oportunidades enviadas a Telegram
  - Errores solo si algo falla

## 8. Limites de responsabilidad por modulo

| Modulo | Responsabilidad | NO hace |
|---|---|---|
| `reddit/` | Conectar con APIs, traer TODOS los posts de `r/Odoo` dentro de 7 dias por fecha de creacion, recuperar comentarios solo para posts ya seleccionados aguas arriba y normalizar al contrato compartido manteniendo marca de incompleto si faltan campos. | NO decide si un post es oportunidad, NO aplica el corte diario a 8, NO mantiene backlog editorial, NO evalua, NO guarda estado por si solo. |
| `evaluation/` | Recibir candidatos normalizados, conectar con DeepSeek (via SDK de OpenAI), aplicar reglas de elegibilidad, devolver resultado estructurado. | NO trae posts, NO envia a Telegram, NO guarda estado. |
| `delivery/` | Recibir oportunidades evaluadas, formatear mensajes, enviar a Telegram y reintentar envios fallidos sin volver a invocar IA. | NO evalua, NO filtra, NO decide que se envia. |
| `persistence/` | Guardar/consultar/purgar memoria operativa minima para unicidad e idempotencia, aplicar TTL. | NO conecta con Reddit, NO mantiene backlog editorial, NO evalua, NO envia. |
| `shared/` | Contratos Pydantic compartidos, tipos comunes. | NO contiene logica de negocio. |
| `config/` | Settings con pydantic-settings, carga de `.env`. | NO contiene logica. |
| `main.py` | Orquesta el flujo diario completo. | NO contiene logica de negocio de ningun modulo. |

## 9. Conexiones externas

| Servicio | Mecanismo |
|---|---|
| Reddit | Varias APIs no oficiales de Reddit consumidas via RapidAPI; la estrategia concreta de seleccion y fallback vive en `docs/integrations/reddit/api-strategy.md`. |
| IA | DeepSeek via SDK de OpenAI (compatible, apuntando a `https://api.deepseek.com`). |
| Telegram | Bot API para envio de mensajes. |

---

## Regla fundamental

> Ningun modulo importa a otro modulo directamente. Solo importan de `shared/` y de `config/`. `main.py` es el unico que conoce a todos y los conecta.
