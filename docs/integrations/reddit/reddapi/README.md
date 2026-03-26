# reddapi

**URL:** https://rapidapi.com/SeasonedCode/api/reddapi  
**Proveedor:** SeasonedCode  
**Plataforma:** RapidAPI

---

## Resumen

La API más documentada públicamente de las cuatro. Tiene un conjunto amplio de endpoints concretos verificados que cubren tanto lectura como escritura. La documentación pública y snippets indexados permiten verificar endpoints reales con sus rutas exactas.

---

## Plan gratuito

| Concepto | Límite |
|---|---|
| Requests/mes | 70 (hard limit) |
| Rate limit | 1000 req/hora |
| Bandwidth | 10240 MB/mes |
| Coste extra | +$0.001 por 1 MB adicional |

**Estimación de viabilidad:** con ~21 requests/día de consumo estimado, el plan gratuito dura aproximadamente **3-4 días**. No viable para uso real continuo.

---

## Autenticación

Vía RapidAPI (header `X-RapidAPI-Key`). Pendiente de verificar si requiere credenciales adicionales de Reddit.

---

## Endpoints relevantes

### Lectura — Posts
| Endpoint | Descripción |
|---|---|
| `GET /api/scrape` | Posts de un subreddit |
| `GET /api/scrape/new` | Posts "new" de un subreddit |
| `GET /api/scrape/top` | Posts "top" de un subreddit |
| `GET /api/rising_posts` | Rising posts de un subreddit |
| `GET /api/scrape_post` | Título y contenido de un post |

### Lectura — Comentarios
| Endpoint | Descripción |
|---|---|
| `GET /api/scrape_post_comments` | Comentarios de un post dado |
| `GET /api/scrape_new_comments_and_its_post_content` | Comentarios nuevos + contenido del post para una URL dada |

### Lectura — Usuarios y subreddits
| Endpoint | Descripción |
|---|---|
| `GET /api/user_info` | Información de un usuario en JSON |
| Búsqueda subreddits | Lista de subreddits con cursor de paginación |

### Escritura (fuera del scope de auto-reddit)
| Endpoint | Descripción |
|---|---|
| `POST /api/comment` | Comentar en un post |
| `POST /api/upvote` | Upvotear un post |
| `POST /api/downvote` | Downvotear un post |
| `POST /api/post_to_subreddit` | Publicar en un subreddit |
| `POST /api/create_account` | Crear cuenta |
| `POST /api/login` | Login |
| Y otros... | |

---

## Ejemplos de requests

Pendiente de pruebas reales contra `r/Odoo`.

---

## Ejemplos de responses

Pendiente de pruebas reales.

---

## Riesgos / dudas

- Plan gratuito insuficiente para uso real continuo (70 req/mes)
- Los endpoints de escritura existen pero están fuera del scope del proyecto (auto-reddit no publica)
- Pendiente verificar si `GET /api/scrape` soporta filtrado por fecha de creación o solo devuelve los más recientes
- Pendiente verificar el formato exacto del JSON de respuesta para posts y comentarios

---

## Encaje con auto-reddit

**Veredicto provisional: candidata principal**

Es la única con endpoints verificados explícitamente para los dos casos de uso clave:
1. **Posts de subreddit:** `GET /api/scrape`, `/api/scrape/new`, `/api/scrape/top` → cubre obtener posts de `r/Odoo`
2. **Comentarios de post:** `GET /api/scrape_post_comments` y `GET /api/scrape_new_comments_and_its_post_content` → cubre obtener comentarios

El endpoint de escritura `POST /api/comment` no se usará — auto-reddit solo lee y el humano publica manualmente.

**Próxima validación:** prueba real de `GET /api/scrape` contra `r/Odoo` para verificar estructura de respuesta y disponibilidad de `created_at` para ordenar por fecha de creación.

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
