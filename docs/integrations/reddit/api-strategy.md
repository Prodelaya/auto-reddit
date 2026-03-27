# Reddit API Strategy

## 1. Resumen ejecutivo

Este documento es la fuente operativa vigente para la integracion con Reddit.

El flujo principal recoge SOLO posts de `r/Odoo`, filtra por `created_at` dentro de los ultimos 7 dias, prioriza por posts mas recientes, NO incluye comentarios en `reddit-candidate-collection` y recupera comentarios SOLO para los posts seleccionados aguas arriba en `thread-context-extraction`.

El proyecto evalua 4 APIs no oficiales de Reddit en RapidAPI, pero el flujo principal actual usa 3 de ellas (`reddit3`, `reddit34`, `reddapi`). `reddit-com` queda fuera del flujo principal. Ninguna API es suficiente por si sola, asi que la estrategia combinada sigue siendo necesaria.

## 2. Autenticacion

- 1 cuenta RapidAPI
- 1 API key compartida para las 4 APIs
- Variable de entorno: `REDDIT_API_KEY`
- Header: `X-RapidAPI-Key`

## 3. Asignacion de responsabilidades

### Regla operativa de unicidad

- No existe backlog explicito ni estado `approved`.
- Change 2 excluye posts ya decididos como `sent` o `rejected`, selecciona los 10 elegibles mas recientes y mantiene unicidad e idempotencia operativa minima, no una cola editorial.
- `rejected` significa rechazo final de negocio por la IA: no aplicar respuesta, post cerrado o sin valor de intervencion. No debe volver a procesarse.
- `not selected today` NO es `rejected`; si el post sigue dentro de la ventana de 7 dias y no esta marcado como `sent` ni `rejected`, manana vuelve a competir normalmente desde la ventana.
- Si Telegram falla despues de que la IA haya aceptado una sugerencia, el comportamiento correcto es reintentar el envio sin reevaluar IA.

### Paso 1 — Posts nuevos de r/Odoo

- **Principal**: `reddit3` → `GET /v1/reddit/posts?url=https://www.reddit.com/r/Odoo/&filter=new`
- **Fallback 1**: `reddapi` → `GET /api/scrape/new?subreddit=odoo&limit=<batch-size>`
- **Fallback 2**: `reddit34` → `GET getPostsBySubreddit?subreddit=odoo&sort=new`
- **Reglas de este paso**: solo `r/Odoo`, filtro por fecha de creacion dentro de 7 dias, priorizacion por recencia, sin comentarios en esta fase y sin recorte a 10 en este change. Si una API no devuelve toda la ventana en una sola llamada, habra que agotar la ventana con mas de una llamada; la tactica exacta queda para el diseno tecnico.
- **Justificacion**: reddit3 tiene el doble de cuota (100 vs 50), shape mas plano, prueba real positiva.

### Paso 2 — Comentarios por post

- **Principal**: `reddit34` → `GET getPostCommentsWithSort?post_url=...&sort=new`
- **Fallback 1**: `reddit3` → `GET /v1/reddit/post?url=...` (post + comentarios, orden cronologico verificado)
- **Fallback 2**: `reddapi` → `GET /api/scrape_new_comments_and_its_post_content?post_url=...`
- **Regla de alcance**: este paso solo se ejecuta para posts ya seleccionados aguas arriba. El caso `post antiguo pero vivo` queda fuera del alcance actual.
- **Justificacion**: reddit34 es la unica con `sort=new` verificado para comentarios recientes reales.

### reddit-com

Descartada del flujo principal. Solo busqueda global con ruido de multiples subreddits.

## 4. Cuotas y reparto mensual

Escenario de referencia para planning: modelo 10/10, ejecucion de lunes a viernes (~22 dias/mes), hasta 10 llamadas diarias de comentarios para los posts que sigan aguas arriba y con el consumo de posts pendiente de recalculo fino si la recoleccion completa de la ventana exige mas de una llamada diaria.

- Consumo de referencia: `~242 req/mes` bajo el supuesto historico de 1 llamada diaria para posts; debe revisarse si la recoleccion completa requiere paginacion o batches adicionales.
- Cuota total disponible combinando las 4 APIs: `320 req/mes`
- Margen combinado estimado: `~78 req/mes`

La presion de cuota se concentra sobre todo en comentarios por post. Por eso `reddit34` actua como principal solo mientras tenga margen y `reddit3` + `reddapi` quedan preparados como absorcion de fallback.

## 5. Cadena de fallback

### Posts

```
reddit3 → reddapi → reddit34 → ABORT (log error, no envia a Telegram, se intenta al dia siguiente)
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

- `scrape_new_comments_and_its_post_content` devuelve top comments, no recientes
- `comments_num` no se respeta estrictamente
- No devuelve `comment_id`, `created_utc` ni `permalink` en comentarios

### reddit34

- Cuota mas ajustada (50 req/mes)
- Mejor API verificada para comentarios recientes con `sort=new`
- Trae replies anidadas con `created`, `depth`, `parent_id`

### reddit3

- Mas versatil de las 4
- `GET /v1/reddit/post?url=...` devuelve post + comentarios en una llamada
- Orden de comentarios verificado como cronologico
- `GET /v1/reddit/subreddit/comments` existe, pero queda fuera del flujo principal actual porque `old but alive` no entra en alcance

### reddit-com

- Solo busqueda global por query
- Devuelve posts de multiples subreddits mezclados
- No util para el flujo principal del MVP

## 11. Parametros provisionales

- `daily_review_limit`: 10 posts/dia (provisionales, revisables tras pruebas reales)
- `max_daily_opportunities`: 10/dia (provisionales)
- Ejecucion: solo lunes-viernes
- Logica de fin de semana en `main.py`, no en cron

## 12. Nota sobre cuentas multiples

Se ha considerado crear multiples cuentas RapidAPI para multiplicar cuota. De momento se trabaja con 1 sola cuenta. Si se verifica que los TOS de RapidAPI lo permiten, esto podria duplicar o triplicar la cuota disponible, pero NO se basa la arquitectura en ello.

## 13. Estado del documento

Este documento refleja las decisiones operativas vigentes tomadas el 27/03/2026. Los valores de cuota y reparto podran revisarse tras uso real, pero el modelo actual de alcance es: `r/Odoo` solo, ventana de 7 dias por fecha de creacion, priorizacion por recencia, comentarios solo para posts seleccionados, change 1 sin recorte a 10 y change 2 aplicando la seleccion diaria de 10 elegibles.
