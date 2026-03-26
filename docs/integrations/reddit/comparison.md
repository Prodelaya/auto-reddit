# Comparativa APIs no oficiales de Reddit

## Resumen de planes gratuitos

| API | Requests gratuitas/mes | Rate limit | Bandwidth |
|---|---|---|---|
| `reddit3` | 100 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `reddit34` | 50 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `reddapi` | 70 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |
| `reddit-com` | 100 / mes (hard limit) | 1000 req/hora | 10240 MB/mes |

## Estimación de consumo del proyecto

Cada ejecución diaria de auto-reddit necesita como mínimo:
- 1 request para traer posts del subreddit
- hasta 20 requests para traer comentarios (1 por post revisado)
- **Total estimado: ~21 requests/día**
- **Total mensual estimado: ~630 requests/mes**

### Conclusión de viabilidad gratuita

| API | Requests gratuitas | Días que aguanta | Viable en gratuito |
|---|---|---|---|
| `reddit3` | 100 | ~5 días | NO |
| `reddit34` | 50 | ~2-3 días | NO |
| `reddapi` | 70 | ~3-4 días | NO |
| `reddit-com` | 100 | ~5 días | NO |

**Ninguna API es viable en plan gratuito para uso real continuo.**
El plan gratuito solo sirve para pruebas puntuales y validación técnica.

---

## Comparativa de cobertura

| API | Documentación pública | Endpoints verificados posts | Endpoints verificados comentarios | Cobertura usuarios | Cobertura búsqueda |
|---|---|---|---|---|---|
| `reddit3` | Muy escasa | Indicios (posts + URL) | Indicios (1 endpoint basado en URL) | Desconocida | Indicios (search) |
| `reddit34` | Catalogo publico util y dos pruebas reales positivas | `getPostsBySubreddit` probado con `sort=new` y shape valido para candidate collection | `getPostCommentsWithSort` probado con `sort=new`; ahora mismo es la mejor candidata para comentarios recientes | Si (profiles, stats, overview) | Si (posts, subreddits, users) |
| `reddapi` | La más completa y verificable | /api/scrape, /api/scrape/new, /api/scrape/top, /api/rising_posts, /api/scrape_post | /api/scrape_post_comments, /api/scrape_new_comments_and_its_post_content | Sí (/api/user_info) | Sí (subreddits con paginación) |
| `reddit-com` | Muy escasa | Desconocida | Desconocida | Desconocida | Desconocida |

---

## Veredicto provisional

| API | Veredicto | Motivo |
|---|---|---|
| `reddapi` | **Muy buena candidata para posts y contexto general** | Sigue teniendo buena cobertura verificable y encaja bien para scraping de posts y contexto alrededor del post |
| `reddit34` | **Candidata muy fuerte, especialmente para comentarios** | Ya tiene prueba real positiva para posts nuevos y prueba real positiva para comentarios recientes con `sort=new` |
| `reddit3` | Exploratoria | Escasa información pública, bajo límite gratuito |
| `reddit-com` | Exploratoria | Muy poca información pública verificable |

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

## Estrategia de uso de APIs

La estrategia final sigue abierta. Con lo verificado hasta ahora, no conviene cerrar aun una asignacion fija de posts y comentarios por API.

Nota de trabajo provisional:

- `ReddAPI` sigue siendo muy buena candidata para posts y contexto general
- `reddit34` es la mejor candidata actual para comentarios recientes
- la arquitectura final podria combinar APIs distintas para posts y comentarios si eso optimiza cobertura y cuota mensual
- la decision final queda abierta hasta investigar `reddit3` y `reddit-com`

## Decisión

- **Estado:** abierto; ya hay validacion real positiva de `reddit34`, pero faltan `reddit3` y `reddit-com`
- **Posts nuevos:** `reddit34` ya demuestra que puede servir; `ReddAPI` sigue bien posicionada para posts/contexto general
- **Comentarios recientes:** `reddit34` pasa a ser la mejor candidata actual por la prueba real de `sort=new`
- **Estrategia final:** no cerrada; podria haber reparto por responsabilidades entre APIs
- **Riesgo principal:** la normalizacion puede tener que soportar contratos distintos si se termina combinando mas de una API
- **Siguiente validacion:** investigar `reddit3` y `reddit-com` antes de fijar API principal o reparto definitivo
