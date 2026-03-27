# Comparativa APIs no oficiales de Reddit

## Resumen de planes gratuitos

| API | Requests gratuitas/mes | Rate limit | Bandwidth |
|---|---|---|---|
| `reddit3` | 100 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `reddit34` | 50 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `ReddAPI` | 70 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `reddit-com` | 100 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |

## Estimación de consumo del proyecto

Cada ejecución diaria de auto-reddit necesita como mínimo:
- 1 request para traer posts del subreddit
- hasta 8 requests para traer comentarios de los posts seleccionados aguas arriba (1 por post como máximo)
- **Total estimado: ~9 requests/día**
- **Total mensual estimado: ~198 requests/mes**

### Conclusión de viabilidad gratuita

| API | Requests gratuitas | Días que aguanta | Viable en gratuito |
|---|---|---|---|
| `reddit3` | 100 | ~11 días laborables | Parcial / con apoyo |
| `reddit34` | 50 | ~5 días laborables | Parcial / con apoyo |
| `ReddAPI` | 70 | ~7-8 días laborables | Parcial / con apoyo |
| `reddit-com` | 100 | ~11 días laborables | Reserva |

**La suma nominal de cuotas sigue siendo 320 req/mes, pero la evidencia operativa ya NO sostiene el modelo 10/10 en gratuito y obliga a bajar la referencia vigente a 8/8.**
Con las probes del 27/03/2026, `reddapi` vuelve a ser util solo si el cliente envia un `User-Agent` aceptado por Cloudflare; eso deja 220 req/mes realmente utilizables para el flujo principal ampliado (`reddit3` + `reddit34` + `reddapi`), aunque parte de esa capacidad recuperada solo aporta un fallback degradado para comentarios.

---

## Comparativa de cobertura

| API | Documentacion publica | Endpoints verificados posts | Endpoints verificados comentarios | Cobertura usuarios | Cobertura busqueda |
|---|---|---|---|---|---|
| `reddit3` | Muy escasa, pero con varias pruebas reales positivas y una senal contradictoria a resolver | `GET /v1/reddit/posts?url=...&filter=new` probado con `200 OK`, `meta.total=25` y `cursor`; `GET /v1/reddit/post?url=...` devuelve post completo | `GET /v1/reddit/post?url=...` devuelve hilo completo con `created_utc`, pero el orden no es estrictamente cronologico; `GET /v1/reddit/subreddit/comments?subreddit=odoo` mostro primero `success=false` y despues `body` real con `cursor`, asi que existe evidencia de inestabilidad de contrato | Desconocida | No verificada en esta ronda |
| `reddit34` | Catalogo publico util y dos pruebas reales positivas | `getPostsBySubreddit` probado con `sort=new` y shape valido para candidate collection | `getPostCommentsWithSort` probado con `sort=new`; ahora mismo es la mejor candidata para comentarios recientes por post, aunque en la muestra hay al menos un comentario con `text` vacio | Si (profiles, stats, overview) | Si (posts, subreddits, users) |
| `ReddAPI` | Bien documentada en catalogo y operativa con condicion de cliente | `/api/scrape/new` devuelve `200 OK` y `cursor` si la llamada incluye un `User-Agent` aceptado por Cloudflare; sin ese header cae en `403 Error 1010` | `/api/scrape_new_comments_and_its_post_content` y `/api/scrape_post_comments` tambien devuelven `200 OK` con ese `User-Agent`, pero hoy entregan una seleccion plana de `top comments`, sin timestamps, ids de comentario, permalinks ni replies; sin ese header, Cloudflare responde `403 Error 1010` | Si en papel, no verificado operativamente ahora | Si en papel, no verificado operativamente ahora |
| `reddit-com` | Escasa, pero con una prueba real util para descarte | `GET /posts/search-posts?query=odoo&sort=new&time=week` devuelve `200 OK` y shape rico, incluyendo posts de `r/Odoo` entre resultados | No verificado como fuente util de comentarios recientes ni de collection por subreddit | Desconocida | Si, pero siempre como busqueda global por query con ruido de otros subreddits y crossposts |

---

## Veredicto provisional

| API | Veredicto | Motivo |
|---|---|---|
| `reddit34` | **Mejor candidata actual para comentarios recientes por post** | La prueba real sigue confirmando `sort=new`, replies anidadas y metadata suficiente para reconstruir contexto; su caveat actual es puntual (`text` vacio en al menos un comentario), no de semantica global |
| `reddit3` | **Fuente operativa mas fuerte para posts y fallback de comentarios** | La prueba real confirma posts de `r/Odoo` y hilo completo, pero obliga a corregir que el orden de comentarios no viene garantizado y que el endpoint de comentarios por subreddit sigue siendo contradictorio |
| `ReddAPI` | **Fallback util, pero degradado y condicionado por `User-Agent`** | Las probes nuevas funcionan solo con un `User-Agent` aceptado por Cloudflare; ademas, en comentarios la evidencia actual apunta a `top comments` sin metadata suficiente para recencia fina |
| `reddit-com` | **Util para exploracion, no para candidate collection del MVP** | La prueba real confirma busqueda global rica por query, pero mezcla `r/Odoo` con otros subreddits y crossposts |

---

## Estimación de consumo ajustada

Con `daily_review_limit = 8` y ejecucion solo dias laborables (lunes-viernes, ~22 dias/mes):
- 1 llamada para traer lista de posts
- 8 llamadas para comentarios
- **Total: 9 llamadas/día → ~198 req/mes**
- Total nominal catalogado combinando las 4 APIs: **320 req/mes**
- Total operativo realmente util hoy para el flujo principal ampliado: **220 req/mes**
- **Margen operativo: ~22 llamadas/mes** antes de sumar paginacion adicional

El sistema no ejecuta sabados ni domingos. La logica de dia laborable vive en `main.py`, no en el cron externo.

**Decision documental vigente para design**: el modelo gratuito 10/10 queda descartado; la referencia operativa pasa a 8/8 para dejar ~22 req/mes de margen antes de paginacion adicional. Si se quisiera volver a subir, haria falta mas cuota o aceptar cobertura parcial/degradada.

## Conclusion provisional

La estrategia operativa mas reciente y fiable ya esta cerrada en `docs/integrations/reddit/api-strategy.md`.

A dia de hoy:

- `reddit3` es la principal para recoger posts nuevos de `r/Odoo`
- `reddit34` es la principal para comentarios por post
- `ReddAPI` queda disponible como fallback condicionado a enviar un `User-Agent` aceptado por Cloudflare, con matiz importante: posts si, comentarios solo en modo degradado
- `reddit-com` queda fuera del flujo principal y solo conserva valor exploratorio

Este documento se conserva como comparativa historica y tecnica de apoyo.
