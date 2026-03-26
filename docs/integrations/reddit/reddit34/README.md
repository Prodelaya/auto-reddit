# reddit34

**URL:** https://rapidapi.com/socialminer/api/reddit34  
**Proveedor:** socialminer  
**Plataforma:** RapidAPI

---

## Resumen

API no oficial de Reddit con 28+ endpoints y cobertura sobre posts, comments, user profiles, subreddit data, search y analytics. Es la segunda más documentada públicamente de las cuatro. No se ha podido verificar el catálogo completo de endpoints ni los esquemas de respuesta campo a campo.

---

## Plan gratuito

| Concepto | Límite |
|---|---|
| Requests/mes | 50 (hard limit) |
| Rate limit | 1000 req/hora |
| Bandwidth | 10240 MB/mes |
| Coste extra | +$0.001 por 1 MB adicional |

**Estimación de viabilidad:** con ~21 requests/día de consumo estimado, el plan gratuito dura aproximadamente **2-3 días**. No viable para uso real continuo. Es el límite gratuito más bajo de las cuatro APIs.

---

## Autenticación

Vía RapidAPI (header `X-RapidAPI-Key`). Pendiente de verificar si requiere algo adicional.

---

## Endpoints relevantes

Catálogo completo no verificable públicamente. Lo que sí se ha podido verificar:

### Posts
- Posts por subreddit o por usuario en varias ordenaciones: popular, top, rising, best, controversial
- Endpoint verificado por nombre: `GET Top Posts By Subreddit`

### Comentarios
- Comentarios de un post con ordenación
- Comentarios por usuario o por subreddit
- Top comments

### Usuarios
- Perfiles y métricas básicas
- Stats, overview
- Post rank in subreddit
- Search users

### Subreddits
- Info del subreddit
- Rules, moderators
- Subreddits similares
- Search subreddits

### Búsqueda
- Search posts, subreddits and users

---

## Ejemplos de requests

Pendiente de pruebas reales.

---

## Ejemplos de responses

Pendiente de pruebas reales.

---

## Riesgos / dudas

- El catálogo completo de 28+ endpoints no está indexado públicamente
- Los nombres exactos de los endpoints y sus parámetros no están todos verificados
- El plan gratuito es el más restrictivo de las cuatro (50 req/mes)
- Sin esquemas de respuesta verificados, el contrato de integración hay que inferirlo en pruebas

---

## Encaje con auto-reddit

**Veredicto provisional: candidata secundaria**

La cobertura funcional descrita públicamente encaja bien con los dos casos de uso clave:
1. traer posts de `r/Odoo` ordenados por fecha de creación → cubierto (posts por subreddit con varias ordenaciones)
2. traer comentarios de un post concreto → cubierto (post comments con sorting)

Pendiente de validar con pruebas reales que los endpoints funcionen como se describe y que el formato de respuesta sea procesable.

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
