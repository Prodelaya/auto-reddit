# Reddit API Strategy

## 1. Resumen ejecutivo

El proyecto usa 4 APIs no oficiales de Reddit en RapidAPI con planes gratuitos. Ninguna es viable sola. La estrategia combina las 4 para cubrir el consumo estimado de ~242 req/mes (10 posts/dia x lunes-viernes x 22 dias), con ~78 req de margen sobre un total disponible de 320 req/mes.

## 2. Autenticacion

- 1 cuenta RapidAPI
- 1 API key compartida para las 4 APIs
- Variable de entorno: `REDDIT_API_KEY`
- Header: `X-RapidAPI-Key`

## 3. Asignacion de responsabilidades

### Paso 1 — Posts nuevos de r/Odoo

- **Principal**: `reddit3` → `GET /v1/reddit/posts?url=https://www.reddit.com/r/Odoo/&filter=new`
- **Fallback 1**: `reddapi` → `GET /api/scrape/new?subreddit=odoo&limit=10`
- **Fallback 2**: `reddit34` → `GET getPostsBySubreddit?subreddit=odoo&sort=new`
- **Justificacion**: reddit3 tiene el doble de cuota (100 vs 50), shape mas plano, prueba real positiva.

### Paso 2 — Comentarios por post

- **Principal**: `reddit34` → `GET getPostCommentsWithSort?post_url=...&sort=new`
- **Fallback 1**: `reddit3` → `GET /v1/reddit/post?url=...` (post + comentarios, orden cronologico verificado)
- **Fallback 2**: `reddapi` → `GET /api/scrape_new_comments_and_its_post_content?post_url=...`
- **Justificacion**: reddit34 es la unica con `sort=new` verificado para comentarios recientes reales.

### reddit-com

Descartada del flujo principal. Solo busqueda global con ruido de multiples subreddits.

## 4. Cuotas y reparto mensual

| API | Req gratuitas/mes | Rol principal | Ruta feliz/mes | Fallback/mes | Reserva |
|---|---|---|---|---|---|
| reddit3 | 100 | Posts nuevos | ~22 | ~10 | ~68 |
| reddit34 | 50 | Comentarios recientes | ~44 | 0 | ~6 |
| reddapi | 70 | Fallback general | 0 | ~42 | ~28 |
| reddit-com | 100 | Reserva/exploracion | 0 | 0 | 100 |
| **Total** | **320** | | **~66** | **~52** | **~202** |

Ruta feliz: ~66 req/mes. Margen total: ~254 req/mes.

reddit34 es la mas ajustada (44 de 50). Cuando se agote, reddit3 absorbe con su endpoint de post + comentarios.

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
- `GET /v1/reddit/subreddit/comments` util para detectar actividad pero lento (~8900 ms)

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

Este documento refleja decisiones tomadas el 27/03/2026 y es provisional. Los valores de cuota, asignaciones y limits se revisaran tras las primeras semanas de uso real.
