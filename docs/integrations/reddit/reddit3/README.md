# reddit3

**URL:** https://rapidapi.com/sparior/api/reddit3  
**Proveedor:** sparior  
**Plataforma:** RapidAPI

---

## Resumen

`reddit3` es una API no oficial de Reddit disponible en RapidAPI:
- API: `reddit3`
- URL RapidAPI: https://rapidapi.com/sparior/api/reddit3
- Plataforma: RapidAPI

Ya no es una opcion opaca: hay 3 pruebas reales positivas que confirman cobertura util para `auto-reddit`.

Lo verificado hasta ahora:
- comentarios recientes de un subreddit: `GET /v1/reddit/subreddit/comments?subreddit=odoo`
- post completo + comentarios por URL: `GET /v1/reddit/post?url=...`
- posts del subreddit con `filter=new`: `GET /v1/reddit/posts?url=https://www.reddit.com/r/Odoo/&filter=new`

Veredicto sugerido: `candidata fuerte y versatil, especialmente util si se quiere combinar deteccion de actividad por comentarios + post completo`.

---

## Plan gratuito

| Concepto | Límite |
|---|---|
| Requests/mes | 100 (hard limit) |
| Rate limit | 1000 req/hora |
| Bandwidth | 10240 MB/mes |
| Coste extra | +$0.001 por 1 MB adicional |

**Estimación de viabilidad:** con ~21 requests/día de consumo estimado, el plan gratuito dura aproximadamente **5 días**. No viable para uso real continuo.

---

## Autenticacion

Autenticacion via RapidAPI con header `X-RapidAPI-Key`.

No hay evidencia documentada en estas pruebas de que haga falta un mecanismo adicional.

---

## Endpoints probados y utiles para auto-reddit

### 1. Comentarios recientes del subreddit

Endpoint probado:

`GET https://reddit3.p.rapidapi.com/v1/reddit/subreddit/comments?subreddit=odoo`

Resultado verificado:
- `200 OK`
- tiempo aproximado: `~8904 ms`
- shape real confirmado:

```json
{
  "meta": {
    "version": "v1.0",
    "status": 200,
    "copywrite": "https://steadyapi.com",
    "subreddit": "odoo",
    "cursor": "t1_oclfa33"
  },
  "body": [
    {
      "id": "ocobl47",
      "author": "Codemarchant",
      "body": "...",
      "created_utc": 1774567283,
      "permalink": "/r/Odoo/comments/.../ocobl47/",
      "link_id": "t3_1s4l6x4",
      "link_title": "Odoo MCP Server",
      "link_permalink": "https://www.reddit.com/r/Odoo/comments/1s4l6x4/odoo_mcp_server/",
      "parent_id": "t3_1s4l6x4",
      "score": 1,
      "replies": ""
    }
  ]
}
```

Conclusiones verificadas:
- sirve para detectar actividad reciente del subreddit a nivel comentario
- devuelve comentarios recientes del subreddit con referencia al post al que pertenecen
- puede ser util para detectar posts activos aunque no sean recien creados
- es el endpoint mas lento probado hasta ahora (`~8904 ms`)

### 2. Post + comentarios por URL

Endpoint probado:

`GET https://reddit3.p.rapidapi.com/v1/reddit/post?url=...`

Resultado verificado:
- `200 OK`
- tiempo aproximado: `~2791 ms`
- shape real confirmado:

```json
{
  "meta": {
    "version": "v1.0",
    "status": 200,
    "copywrite": "https://steadyapi.com",
    "totalComments": 21
  },
  "body": {
    "post": {
      "id": "1s308bl",
      "title": "...",
      "selftext": "...",
      "url": "https://www.reddit.com/...",
      "permalink": "/r/Odoo/comments/...",
      "created_utc": 1774410836,
      "num_comments": 21
    },
    "post_comments": [
      {
        "id": "occplnx",
        "author": "gurthang2",
        "score": 23,
        "created_utc": 1774424048,
        "content": "...",
        "replies": []
      }
    ]
  }
}
```

Conclusiones verificadas:
- sirve para obtener un hilo completo a partir de la URL del post
- devuelve post + comentarios en una sola llamada
- trae replies anidadas
- trae `created_utc` tambien en comentarios
- aun falta validar si el orden de `post_comments` responde a criterio cronologico, `new`, `top` u otro criterio

### 3. Posts del subreddit

Endpoint probado:

`GET https://reddit3.p.rapidapi.com/v1/reddit/posts?url=https://www.reddit.com/r/Odoo/&filter=new`

Resultado verificado:
- `200 OK`
- tiempo aproximado: `~3090 ms`
- shape real confirmado:

```json
{
  "meta": {
    "version": "v1.0",
    "status": 200,
    "copywrite": "https://steadyapi.com",
    "total": 25,
    "cursor": "t3_1s2h2t3"
  },
  "body": [
    {
      "id": "1s4l6x4",
      "title": "...",
      "selftext": "...",
      "author": "Kindly-Jacket-429",
      "num_comments": 2,
      "url": "https://www.reddit.com/...",
      "permalink": "/r/Odoo/comments/...",
      "created_utc": 1774562157
    }
  ]
}
```

Conclusiones verificadas:
- sirve para candidate collection
- `filter=new` funciona en la practica
- trae los campos minimos necesarios para el primer slice

Catalogo completo: sigue sin estar bien documentado publicamente, pero estos 3 endpoints ya quedan verificados con pruebas reales positivas.

---

## Que sirve para auto-reddit y por que

`reddit3` sirve para tres necesidades distintas del proyecto:

1. traer posts nuevos del subreddit para candidate collection
2. traer un post concreto con sus comentarios en una sola llamada
3. detectar actividad reciente a nivel subreddit a traves de comentarios recientes

Esto lo hace mas versatil de lo esperado porque permite cubrir tanto discovery por posts nuevos como discovery por actividad reciente en comentarios.

En especial:
- `GET /v1/reddit/posts?...&filter=new` encaja con el primer slice de seleccion de candidatos
- `GET /v1/reddit/post?url=...` encaja con enriquecimiento de un hilo concreto
- `GET /v1/reddit/subreddit/comments?...` encaja con deteccion de posts activos aunque no sean recien creados

La combinacion de post completo + actividad reciente por comentarios le da un valor diferencial frente a APIs que solo cubren uno de los dos planos.

---

## Riesgos / dudas

- documentacion publica muy escasa fuera de las pruebas hechas
- el endpoint de comentarios recientes del subreddit es el mas lento probado hasta ahora (`~8904 ms`)
- aun falta validar si el orden de comentarios en `GET /v1/reddit/post` responde a criterio cronologico o no
- el plan gratuito sigue siendo insuficiente para uso real continuo

---

## Encaje con auto-reddit

**Veredicto provisional: candidata fuerte y versatil, especialmente util si se quiere combinar deteccion de actividad por comentarios + post completo**

Encaje actual:
- ya hay prueba real positiva para posts nuevos del subreddit
- ya hay prueba real positiva para post + comentarios por URL
- ya hay prueba real positiva para comentarios recientes del subreddit

Eso deja a `reddit3` como una opcion real para una arquitectura mixta donde distintas APIs cubran responsabilidades diferentes.

Decision aun abierta:
- puede servir para posts nuevos
- puede servir para traer el hilo completo de un candidato
- puede servir para detectar actividad reciente a nivel subreddit
- aun falta decidir si conviene usarla tambien para comentarios por post frente a `reddit34`, que sigue siendo la mejor candidata actual para comentarios recientes por post

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
