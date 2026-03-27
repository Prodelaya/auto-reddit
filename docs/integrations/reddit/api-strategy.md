# Reddit API Strategy

## 1. Resumen ejecutivo

Este documento es la fuente operativa vigente para la integracion con Reddit.

El flujo principal recoge SOLO posts de `r/Odoo`, filtra por `created_at` dentro de los ultimos 7 dias, prioriza por posts mas recientes, NO incluye comentarios en `reddit-candidate-collection` y recupera comentarios SOLO para los posts seleccionados aguas arriba en `thread-context-extraction`.

El proyecto evalua 4 APIs no oficiales de Reddit en RapidAPI. La evidencia mas reciente mantiene `reddit3` y `reddit34` como fuentes principales del flujo, confirma que `reddapi` vuelve a ser operativa si el cliente envia un `User-Agent` aceptado por Cloudflare (por ejemplo `RapidAPI Playground`) y mantiene `reddit-com` fuera del flujo principal por su naturaleza de busqueda global con ruido. La recuperacion de `reddapi` NO la convierte en equivalente funcional de `reddit34` para comentarios recientes: hoy sirve mejor como fallback degradado y condicionado por endpoint. Ninguna API es suficiente por si sola, y el supuesto historico de viabilidad gratuita 10/10 queda reemplazado por el cap operativo vigente de 8/8.

## 2. Autenticacion

- 1 cuenta RapidAPI
- 1 API key compartida para las 4 APIs
- Variable de entorno: `REDDIT_API_KEY`
- Header: `X-RapidAPI-Key`

## 3. Asignacion de responsabilidades

### Regla operativa de unicidad

- No existe backlog explicito ni estado `approved`.
- Change 2 excluye posts ya decididos como `sent` o `rejected`, selecciona los 8 elegibles mas recientes y mantiene unicidad e idempotencia operativa minima, no una cola editorial.
- `rejected` significa rechazo final de negocio por la IA: no aplicar respuesta, post cerrado o sin valor de intervencion. No debe volver a procesarse.
- `not selected today` NO es `rejected`; si el post sigue dentro de la ventana de 7 dias y no esta marcado como `sent` ni `rejected`, manana vuelve a competir normalmente desde la ventana.
- Si Telegram falla despues de que la IA haya aceptado una sugerencia, el comportamiento correcto es reintentar el envio sin reevaluar IA.

### Paso 1 — Posts nuevos de r/Odoo

- **Principal**: `reddit3` → `GET /v1/reddit/posts?url=https://www.reddit.com/r/Odoo/&filter=new`
- **Fallback 1**: `reddit34` → `GET getPostsBySubreddit?subreddit=odoo&sort=new`
- **Fallback 2**: `reddapi` → `GET /api/scrape/new?subreddit=odoo&limit=<batch-size>` devuelve `200 OK` y `cursor` si la llamada incluye un `User-Agent` aceptado por Cloudflare; sin ese header responde `403 Error 1010`
- **Reglas de este paso**: solo `r/Odoo`, filtro por fecha de creacion dentro de 7 dias, priorizacion por recencia, sin comentarios en esta fase y sin recorte a 8 en este change. Si una API no devuelve toda la ventana en una sola llamada, habra que agotar la ventana con mas de una llamada; la tactica exacta queda para el diseno tecnico.
- **Justificacion**: reddit3 sigue siendo la mejor fuente operativa para posts (`200 OK`, shape plano, `meta.total=25`, `cursor` presente). reddit34 queda como respaldo operativo tambien verificado con `200 OK` y `cursor`, aunque con shape mas anidado y mitad de cuota.

### Paso 2 — Comentarios por post

- **Principal**: `reddit34` → `GET getPostCommentsWithSort?post_url=...&sort=new`
- **Fallback 1**: `reddit3` → `GET /v1/reddit/post?url=...` (post + comentarios completos; requiere reordenar si hiciera falta recencia estricta)
- **Fallback 2**: `reddapi` → `GET /api/scrape_new_comments_and_its_post_content?post_url=...` o `GET /api/scrape_post_comments?post_url=...` devuelven `200 OK` si la llamada incluye un `User-Agent` aceptado por Cloudflare; sin ese header responden `403 Error 1010`
- **Regla de alcance**: este paso solo se ejecuta para posts ya seleccionados aguas arriba. El caso `post antiguo pero vivo` queda fuera del alcance actual.
- **Justificacion**: reddit34 es la unica con `sort=new` verificado para comentarios recientes reales. La probe reciente devuelve comentarios top-level en recencia descendente y conserva replies con `depth`, `parent_id` y `permalink` completos. `reddapi` queda por debajo porque sus endpoints de comentarios hoy devuelven una seleccion plana de `top comments`, sin `comment_id`, `created`, `permalink` ni arbol de replies, asi que solo sirven como contexto degradado, no como sustituto reproducible de recencia por comentario.

### reddit-com

Descartada del flujo principal. La probe reciente confirma `200 OK` y resultados ricos, pero siguen mezclados posts de multiples subreddits y crossposts; sirve como busqueda global exploratoria, no como candidate collection limpia de `r/Odoo`.

## 4. Cuotas y reparto mensual

Escenario de referencia vigente para planning: modelo 8/8, ejecucion de lunes a viernes (~22 dias/mes), hasta 8 llamadas diarias de comentarios para los posts que sigan aguas arriba y con el consumo de posts pendiente de recalculo fino si la recoleccion completa de la ventana exige mas de una llamada diaria.

- Consumo de referencia vigente: `~198 req/mes` bajo el supuesto de 1 llamada diaria para posts (`22` de posts + `176` de comentarios); debe revisarse si la recoleccion completa requiere paginacion o batches adicionales.
- Capacidad nominal catalogada combinando las 4 APIs: `320 req/mes`
- Capacidad operativa util con evidencia real del 27/03/2026 tras corregir el cliente de `reddapi`: `220 req/mes` (`reddit3` 100 + `reddit34` 50 + `reddapi` 70)
- Margen operativo frente al modelo 8/8: `~22 req/mes` antes de contar paginacion adicional

La presion de cuota se concentra sobre todo en comentarios por post. Incluso recuperando `reddapi` con el `User-Agent` correcto, el flujo gratuito actual no deja margen suficiente para el modelo historico 10/10; por eso la referencia operativa vigente baja a 8/8. Aun asi, la cuota recuperada de `reddapi` no compra el mismo nivel de calidad para comentarios recientes que `reddit34`, asi que cualquier crecimiento futuro exigira o mas cuota o una degradacion asumida de cobertura/calidad.

## 5. Cadena de fallback

### Posts

```
reddit3 → reddit34 → reddapi → ABORT (log error, no envia a Telegram, se intenta al dia siguiente)
```

### Comentarios por post

```
reddit34 → reddit3 → reddapi → SKIP post (log warning, continua con siguiente post)
```

## 6. Control de cuota

- Contador interno por API y por mes (resetea el dia 1 de cada mes)
- Ademas, deteccion de errores HTTP 429/403 como backup
- Si el contador interno indica agotamiento, se salta la API directamente sin llamar

## 7. Retry policy

- Maximo 2 retries por llamada
- Backoff: 2 segundos → 4 segundos
- Si falla tras 2 retries → pasa al fallback
- Un retry cuenta como request para el contador de cuota

## 8. Comportamiento en fallo total

Si todas las APIs fallan o estan agotadas para un paso:

- **Posts**: ABORT silencioso, log de error, no se envia nada a Telegram
- Se intenta de nuevo al dia siguiente
- No se envia alerta a Telegram

## 9. Normalizacion

### Post normalizado

```python
class RedditPost(BaseModel):
    post_id: str
    title: str
    selftext: str
    author: str
    url: str               # URL completa siempre
    permalink: str          # URL completa siempre
    created_utc: int
    num_comments: int
    subreddit: str
    source_api: str
```

Contrato minimo funcional del change 1:

- `post_id`
- `title`
- `body/selftext`
- `url/permalink`
- `author`
- `subreddit`
- `created_at`

Si faltan campos, el post se conserva con marca de incompleto en lugar de descartarse.

### Comentario normalizado

```python
class RedditComment(BaseModel):
    comment_id: str | None     # None si reddapi
    author: str
    body: str                  # normalizado desde text/content/body/comment
    score: int
    created_utc: int | None    # None si reddapi
    permalink: str | None      # URL completa o None
    parent_id: str | None
    depth: int | None
    source_api: str
```

Nota: reddapi no devuelve `comment_id`, `created_utc` ni `permalink` en comentarios. El pipeline debe ser tolerante a `None`.

### Reglas de normalizacion

- Permalink siempre como URL completa (`https://www.reddit.com/...`)
- Si la API devuelve permalink relativo, se prefija con `https://www.reddit.com`
- El campo de texto del comentario se normaliza al campo `body` independientemente de si la API lo llama `text`, `content`, `body` o `comment`
- El ID del comentario se normaliza sin prefijo `t1_` (reddit34 lo incluye, las demas no)
- La salida de `reddit-candidate-collection` se entrega como lista normalizada en memoria/proceso para el siguiente paso

## 10. Limitaciones documentadas por API

### reddapi

- Las 3 probes de `reddapi` (`/api/scrape/new`, `/api/scrape_new_comments_and_its_post_content`, `/api/scrape_post_comments`) pasan de `403 Error 1010` a `200 OK` cuando el cliente replica un `User-Agent` aceptado por Cloudflare (`RapidAPI Playground` en los raws actuales)
- Sin ese `User-Agent`, el error sigue marcando `retryable=false` y `owner_action_required=true`; operativamente significa que no vale insistir con retries ciegos, hay que corregir firma de cliente
- `GET /api/scrape/new` si queda verificado como fuente usable de posts por subreddit tras el fix: devuelve lote de posts de `r/Odoo`, metadata rica y `cursor`
- Los 2 endpoints de comentarios de `reddapi` NO equivalen a `sort=new`: en los raws actuales el payload combinado etiqueta el bloque como `top comments`, el orden no coincide con la recencia observada en `reddit34`, no trae timestamps, tampoco trae `comment_id` ni `permalink`, y pierde la estructura de replies
- Decision operativa: `reddapi` se recupera como fallback real para posts y como fallback degradado para contexto de comentarios, no como fuente principal de comentarios recientes

### reddit34

- Cuota mas ajustada (50 req/mes)
- Mejor API verificada para comentarios recientes con `sort=new`
- Trae replies anidadas con `created`, `depth`, `parent_id`
- En la misma muestra un comentario (`t1_ocoqaq4`) llega con `text=""` aunque el contenido existe en otras APIs; el pipeline debe tolerar comentarios vacios sin asumir corrupcion global del endpoint
- En posts por subreddit tambien devuelve `cursor`, asi que la paginacion queda viable si hiciera falta ampliar ventana

### reddit3

- Mas versatil de las 4
- `GET /v1/reddit/post?url=...` devuelve post + comentarios en una llamada
- El array de comentarios de `GET /v1/reddit/post?url=...` NO sale en orden estrictamente cronologico; sirve como fallback porque trae el hilo completo con `created_utc`, pero si hiciera falta recencia estricta habria que reordenar en cliente
- `GET /v1/reddit/subreddit/comments?subreddit=odoo` ya no puede marcarse como simplemente invalido: una probe anterior devolvio `200` con `success=false` y mensaje `Please enter a valid subReddit URL.`, pero las probes mas recientes devuelven `200` con `body` real y `cursor`; el contrato existe, pero sigue siendo inestable/contradictorio y no debe entrar en design sin validacion adicional

### reddit-com

- Solo busqueda global por query
- Devuelve posts de multiples subreddits mezclados
- No util para el flujo principal del MVP

## 11. Parametros provisionales

- `daily_review_limit`: 8 posts/dia (referencia operativa vigente para design)
- `max_daily_opportunities`: 8/dia (referencia operativa vigente para design)
- Ejecucion: solo lunes-viernes
- Logica de fin de semana en `main.py`, no en cron

## 12. Nota sobre cuentas multiples

Se ha considerado crear multiples cuentas RapidAPI para multiplicar cuota. De momento se trabaja con 1 sola cuenta. Si se verifica que los TOS de RapidAPI lo permiten, esto podria duplicar o triplicar la cuota disponible, pero NO se basa la arquitectura en ello.

## 13. Estado del documento

Este documento refleja las decisiones operativas vigentes tomadas el 27/03/2026. Los valores de cuota y reparto podran revisarse tras uso real, pero con la evidencia actual el alcance sigue siendo `r/Odoo` solo, ventana de 7 dias por fecha de creacion, priorizacion por recencia y comentarios solo para posts seleccionados; lo que cambia es que `reddapi` deja de estar bloqueada si se firma como el cliente aceptado, aunque su recuperacion no resuelve por si sola la tension de cuota ni sustituye la calidad de `reddit34` para comentarios recientes.
