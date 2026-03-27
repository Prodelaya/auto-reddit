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
- hasta 10 requests para traer comentarios de los posts seleccionados aguas arriba (1 por post como máximo)
- **Total estimado: ~11 requests/día**
- **Total mensual estimado: ~242 requests/mes**

### Conclusión de viabilidad gratuita

| API | Requests gratuitas | Días que aguanta | Viable en gratuito |
|---|---|---|---|
| `reddit3` | 100 | ~9 días laborables | Parcial / con apoyo |
| `reddit34` | 50 | ~4-5 días laborables | Parcial / con apoyo |
| `ReddAPI` | 70 | ~6 días laborables | Parcial / con apoyo |
| `reddit-com` | 100 | ~9 días laborables | Reserva |

**Ninguna API es suficiente por si sola para uso continuo, pero la combinacion de varias APIs si encaja en el modelo operativo actual de 10/10.**
El plan gratuito combinado sirve para el slice actual mientras se mantenga la estrategia documentada en `docs/integrations/reddit/api-strategy.md`.

---

## Comparativa de cobertura

| API | Documentacion publica | Endpoints verificados posts | Endpoints verificados comentarios | Cobertura usuarios | Cobertura busqueda |
|---|---|---|---|---|---|
| `reddit3` | Muy escasa, pero con 3 pruebas reales positivas | `GET /v1/reddit/posts?url=...&filter=new` probado con `200 OK` y shape valido para candidate collection; `GET /v1/reddit/post?url=...` devuelve post completo | `GET /v1/reddit/post?url=...` devuelve comentarios del hilo; `GET /v1/reddit/subreddit/comments?subreddit=odoo` devuelve comentarios recientes del subreddit | Desconocida | No verificada en esta ronda |
| `reddit34` | Catalogo publico util y dos pruebas reales positivas | `getPostsBySubreddit` probado con `sort=new` y shape valido para candidate collection | `getPostCommentsWithSort` probado con `sort=new`; ahora mismo es la mejor candidata para comentarios recientes por post | Si (profiles, stats, overview) | Si (posts, subreddits, users) |
| `ReddAPI` | Bien documentada y util | `/api/scrape`, `/api/scrape/new`, `/api/scrape/top`, `/api/rising_posts`, `/api/scrape_post` | `/api/scrape_post_comments`, `/api/scrape_new_comments_and_its_post_content` | Si (`/api/user_info`) | Si (subreddits con paginacion) |
| `reddit-com` | Escasa, pero ya con una prueba real de busqueda global | `GET /posts/search-posts?query=odoo&sort=new&time=week` devuelve `200 OK` y un shape rico para posts | No verificado como fuente util de comentarios recientes ni de collection por subreddit | Desconocida | Si, via busqueda global por query |

---

## Veredicto provisional

| API | Veredicto | Motivo |
|---|---|---|
| `reddit34` | **Mejor candidata actual para comentarios recientes por post** | Ya tiene prueba real positiva para posts nuevos y prueba real positiva para comentarios recientes con `sort=new` |
| `reddit3` | **Candidata fuerte y versatil** | Ya tiene prueba real positiva para posts nuevos, post + comentarios y comentarios recientes del subreddit |
| `ReddAPI` | **Bien documentada y util como fallback** | Mantiene buena cobertura verificable, pero ahora mismo encaja peor que `reddit34` y `reddit3` para el flujo principal actual basado en posts recientes por fecha de creacion y comentarios por post |
| `reddit-com` | **Util para busqueda global, poco adecuada para candidate collection del MVP** | La prueba real confirma busqueda global rica por query, pero no una via limpia para recuperar directamente `r/Odoo` |

---

## Estimación de consumo ajustada

Con `daily_review_limit = 10` y ejecución solo días laborables (lunes-viernes, ~22 días/mes):
- 1 llamada para traer lista de posts
- 10 llamadas para comentarios
- **Total: 11 llamadas/día → ~242 req/mes**
- Total disponible combinando las 4 APIs: **320 req/mes**
- **Margen: ~78 llamadas/mes**

El sistema no ejecuta sábados ni domingos. La lógica de día laborable vive en `main.py`, no en el cron externo.

**Revisable** tras pruebas reales con las APIs para ajustar el límite según cobertura y calidad de respuesta.

## Conclusion provisional

La estrategia operativa mas reciente y fiable ya esta cerrada en `docs/integrations/reddit/api-strategy.md`.

A dia de hoy:

- `reddit3` es la principal para recoger posts nuevos de `r/Odoo`
- `reddit34` es la principal para comentarios por post
- `ReddAPI` queda como fallback general
- `reddit-com` queda fuera del flujo principal y solo conserva valor exploratorio

Este documento se conserva como comparativa historica y tecnica de apoyo.
