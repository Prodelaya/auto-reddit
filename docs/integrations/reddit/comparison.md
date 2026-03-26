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
| `reddit34` | Buena descripción, sin catálogo completo | Posts por subreddit/usuario, ordenaciones múltiples | Post comments, comments by user/subreddit, top comments | Sí (profiles, stats, overview) | Sí (posts, subreddits, users) |
| `reddapi` | La más completa y verificable | /api/scrape, /api/scrape/new, /api/scrape/top, /api/rising_posts, /api/scrape_post | /api/scrape_post_comments, /api/scrape_new_comments_and_its_post_content | Sí (/api/user_info) | Sí (subreddits con paginación) |
| `reddit-com` | Muy escasa | Desconocida | Desconocida | Desconocida | Desconocida |

---

## Veredicto provisional

| API | Veredicto | Motivo |
|---|---|---|
| `reddapi` | **Candidata principal** | Mejor cobertura verificable, endpoints concretos de posts y comentarios |
| `reddit34` | **Candidata secundaria** | Buena cobertura funcional, pero sin catálogo verificable completo |
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

Se usará la **Opción A: API principal + fallback** en cadena:

| Prioridad | API | Requests/mes | Rol |
|---|---|---|---|
| 1 | `reddapi` | 70 | Principal |
| 2 | `reddit3` | 100 | Fallback 1 |
| 3 | `reddit-com` | 100 | Fallback 2 |
| 4 | `reddit34` | 50 | Fallback 3 (último por menor cupo) |
| **Total** | | **320** | |

El sistema usará `reddapi` por defecto. Solo pasará al siguiente cuando el cupo del anterior se haya agotado.

## Decisión

- **Estado:** pendiente de validación con pruebas reales
- **API principal:** `reddapi` — única con endpoints verificados para posts y comentarios
- **Cadena de fallback:** `reddapi` → `reddit3` → `reddit-com` → `reddit34`
- **Motivo del orden:** reddapi es la más fiable documentalmente; reddit34 queda al final por tener el menor cupo gratuito (50/mes)
- **Riesgo principal:** si una API devuelve formato distinto a las demás, la normalización debe cubrir todos los casos
- **Siguiente validación:** prueba real de `reddapi GET /api/scrape` contra `r/Odoo` para verificar estructura de respuesta
