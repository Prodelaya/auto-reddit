# reddit34

**URL:** https://rapidapi.com/socialminer/api/reddit34  
**Proveedor:** socialminer  
**Plataforma:** RapidAPI

## Resumen

`reddit34` ya tiene dos pruebas reales positivas relevantes para `auto-reddit`: una para posts por subreddit con `sort=new` y otra para comentarios de un post con `sort=new`. A dia de hoy es una candidata muy fuerte, especialmente para comentarios, porque devuelve comentarios recientes de forma util y con un shape procesable.

> Estado actual: la decision operativa vigente ya esta cerrada en `docs/integrations/reddit/api-strategy.md`. Este README se conserva como soporte tecnico de la investigacion.

## Plan gratuito

| Concepto | Limite |
|---|---|
| Requests/mes | 50 (hard limit) |
| Rate limit | 1000 req/hora |
| Bandwidth | 10240 MB/mes |
| Coste extra | +$0.001 por 1 MB adicional |

Con el modelo operativo actual, este plan gratuito no sirve por si solo para uso continuo, pero si encaja como API principal de comentarios dentro de una estrategia combinada.

## Autenticacion

Via RapidAPI con header `X-RapidAPI-Key`.

## Catalogo relevante para auto-reddit

Documentacion publica / catalogo disponible verificado en esta investigacion:

- `GET Popular Posts`
- `GET Top Popular Posts`
- `GET Rising Popular Posts`
- `GET Top Posts By Username`
- `GET Posts By Subreddit`
- `GET Top Posts By Subreddit`
- `GET Posts By Username`
- `GET Post Details`
- `GET Comments By Username`
- `GET Top Comments By Username`
- `GET Similar Subreddits`
- `GET Post Duplicates`
- `GET Subreddit Moderators`
- `GET Subreddit Rules`
- `GET User Overview`
- `GET Search Users`
- `GET Best Popular Posts`
- `GET Controversial Posts By Subreddit`
- `GET User Post Rank In Subreddit`
- `GET Subreddit Info`
- `GET Comments By Subreddit`
- `GET Post Comments With Sort`
- `GET Profile`
- `GET Post Comments`
- `GET User Stats`
- `GET Search Posts`
- `GET Search Subreddits`
- `GET New Subreddits`
- `GET Popular Subreddits`

Para `auto-reddit`, lo mas relevante del catalogo publico es que cubre posts por subreddit, detalle de post, comentarios de post con sorting, comentarios por subreddit, perfiles y busquedas auxiliares.

## Pruebas reales verificadas

### 1. Posts por subreddit

Endpoint probado:

`GET https://reddit34.p.rapidapi.com/getPostsBySubreddit?subreddit=odoo&sort=new`

Resultado verificado:

- `200 OK`
- ~`2033 ms`
- shape real confirmado:

```json
{
  "success": true,
  "data": {
    "cursor": "t3_1s2h2t3",
    "posts": [
      {
        "data": {
          "id": "1s4l6x4",
          "title": "...",
          "selftext": "...",
          "author": "...",
          "num_comments": 2,
          "url": "https://www.reddit.com/...",
          "permalink": "/r/Odoo/comments/...",
          "created": 1774562157,
          "created_utc": 1774562157,
          "subreddit": "Odoo",
          "subreddit_name_prefixed": "r/Odoo"
        },
        "kind": "t3"
      }
    ]
  }
}
```

Conclusiones verificadas:

- sirve para candidate collection
- `sort=new` funciona en la practica
- trae `created_utc`, `id`, `selftext`, `url`, `permalink`, `num_comments`
- el shape es muy parecido al listing nativo de Reddit

### 2. Comentarios ordenados por recientes

Endpoint probado:

`GET https://reddit34.p.rapidapi.com/getPostCommentsWithSort?post_url=...&sort=new`

Resultado verificado:

- `200 OK`
- ~`1396 ms`
- shape real confirmado:

```json
{
  "success": true,
  "data": {
    "cursor": null,
    "comments": [
      {
        "author": "spacey003",
        "created": "2026-03-26T08:13:08.906000+0000",
        "depth": 0,
        "id": "t1_ocjlvk6",
        "media": [],
        "parent_id": "",
        "permalink": "https://www.reddit.com/r/Odoo/comments/.../comment/.../",
        "replies": [],
        "score": 1,
        "text": "..."
      }
    ]
  }
}
```

Conclusiones verificadas:

- `sort=new` devuelve comentarios realmente recientes, contrastado manualmente con Reddit
- trae `created`, `id`, `permalink`, `depth`, `parent_id`, `replies`, `score`, `text`
- es mucho mas util que `ReddAPI` para el objetivo ideal de usar comentarios recientes
- puede devolver replies anidadas

## Que sirve para auto-reddit y por que

Sirve bien para dos necesidades clave del sistema:

1. coleccion de candidatos desde `r/Odoo`, porque la prueba real de posts por subreddit ya confirma `sort=new` y un contrato util para extraer fecha, texto, URL y metadatos
2. analisis de comentarios recientes por post, porque la prueba real de comentarios confirma ordenacion por novedad y campos utiles para filtrar, enlazar y recorrer hilos

Ahora mismo es la API principal vigente para comentarios por post dentro del flujo actual.

## Riesgos / dudas

- el plan gratuito sigue siendo muy pequeno para operacion continua
- solo hay parametros verificados en los endpoints probados; no conviene asumir parametros del resto del catalogo sin test real
- aunque el shape de posts se parece mucho al nativo de Reddit, hay que validar mas casos reales si esta API termina entrando en produccion

## Encaje con auto-reddit

**Veredicto vigente: principal para comentarios por post**

Encaja muy bien como fuente de comentarios recientes y queda establecida como la API principal para `thread-context-extraction`. Su uso para candidate collection queda como capacidad secundaria, no como la opcion operativa elegida.

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigacion.
