# reddapi

## Fuentes verificadas

- Documentacion publica: `https://reddapi.online/docs/`
- Documentacion de API: `https://reddapi.online/api/docs`

Este documento resume solo lo verificado con documentacion publica y pruebas reales sobre endpoints utiles para `auto-reddit`.

## Veredicto

ReddAPI es la mejor candidata actual para la integracion de lectura de Reddit en `auto-reddit`.

La razon no es que sea perfecta, sino que combina dos cosas que ahora mismo pesan mas que el resto:

- documentacion publica verificable
- pruebas reales positivas sobre los endpoints que necesita el pipeline

## Que endpoints sirven realmente para auto-reddit

### 1. Candidate collection

Endpoint:

`GET /api/scrape/new`

Uso en `auto-reddit`:

- recoger posts nuevos de `r/Odoo`
- ordenar o filtrar por fecha de creacion usando `created_utc`
- guardar `id` nativo de Reddit como `post_id`
- capturar contenido y metadatos suficientes para el primer slice

Prueba real verificada:

`GET /api/scrape/new?subreddit=odoo&limit=10`

Resultado observado:

- `200 OK`
- ~`2604 ms`
- `proxy` no fue necesario en la practica

Shape real confirmado:

```json
{
  "success": true,
  "cursor": "...",
  "posts": [
    {
      "kind": "t3",
      "data": {
        "id": "1s4l6x4",
        "title": "...",
        "selftext": "...",
        "author": "...",
        "num_comments": 1,
        "url": "https://www.reddit.com/...",
        "permalink": "/r/Odoo/comments/...",
        "created": 1774562157,
        "created_utc": 1774562157,
        "subreddit": "Odoo",
        "subreddit_name_prefixed": "r/Odoo"
      }
    }
  ]
}
```

Por que sirve:

- devuelve posts nuevos del subreddit objetivo
- incluye `created_utc`, asi que SI permite trabajar con orden temporal real
- incluye `id`, `url`, `selftext` y metadatos suficientes para iniciar el pipeline sin otra llamada inmediata

### 2. Thread context extraction

Endpoint:

`GET /api/scrape_new_comments_and_its_post_content`

Uso en `auto-reddit`:

- obtener en una sola llamada el contenido del post y los comentarios usados como contexto del hilo
- reducir round-trips en el pipeline
- simplificar la extraccion de contexto para evaluacion posterior

Prueba real verificada:

`GET /api/scrape_new_comments_and_its_post_content?post_url=...&comments_num=10`

Resultado observado:

- `200 OK`
- ~`890 ms` en una prueba
- ~`2080 ms` en otra
- `proxy` no fue necesario

Shape real confirmado:

```json
{
  "success": true,
  "data": {
    "post content": {
      "subreddit": "r/Odoo",
      "title": "...",
      "text": "..."
    },
    "top comments": [
      {
        "comment": "...",
        "author": "...",
        "user_id": "t2_...",
        "score": 24
      }
    ]
  }
}
```

Lo importante aqui es la semantica real:

- aunque el nombre del endpoint habla de `new comments`, la respuesta devuelve la clave `top comments`
- por comparacion manual con Reddit, los comentarios recuperados coinciden con top comments, no con los mas nuevos
- `comments_num=10` no se respeto estrictamente: devolvio 11 comentarios

Por que sirve igualmente:

- para v1 reduce a una sola llamada el contexto del post + comentarios
- en `r/Odoo` es raro encontrar posts con muchos comentarios
- por eso, en la mayoria de casos, la diferencia entre top comments y comentarios recientes probablemente no afectara mucho

Decision de producto:

- el objetivo ideal del producto sigue siendo usar comentarios recientes si una API fiable los expone en el futuro
- para ReddAPI se trabajara pragmaticamente con los comentarios que realmente devuelve la API, que en la practica son top comments

### 3. Endpoint auxiliar de comentarios

Endpoint:

`GET /api/scrape_post_comments`

Uso en `auto-reddit`:

- endpoint auxiliar de contraste o fallback
- sirve para validar o comparar la salida de comentarios frente al endpoint combinado

Prueba real verificada:

`GET /api/scrape_post_comments?post_url=...&comments_num=10`

Resultado observado:

- `200 OK`
- ~`1386 ms`
- `proxy` no fue necesario

Shape real confirmado:

```json
{
  "success": true,
  "comments": [
    {
      "comment": "...",
      "author": "...",
      "user_id": "t2_...",
      "score": 23
    }
  ]
}
```

Limitaciones observadas:

- devuelve comentarios en un formato simple y util
- no devuelve `comment_id`, `created_utc` ni permalink
- `comments_num=10` tampoco se respeto estrictamente: devolvio 11 comentarios

## Como se usara en el pipeline

### Flujo previsto para v1

1. `GET /api/scrape/new` para recoger candidatos nuevos de `r/Odoo`
2. guardar `post_id` desde `data.id` y usar `created_utc` para el orden temporal
3. `GET /api/scrape_new_comments_and_its_post_content` para extraer contexto del hilo en una sola llamada
4. usar `GET /api/scrape_post_comments` solo como contraste o fallback cuando convenga validar la salida de comentarios

## Riesgos y limites que hay que asumir

- la semantica de `new comments` no es fiable en `GET /api/scrape_new_comments_and_its_post_content`
- `comments_num` no es exacto
- faltan campos importantes en comentarios, como `created_utc`, permalink o un `comment_id` util
- aun asi, la API sigue siendo la mejor candidata actual por combinacion de documentacion publica y pruebas reales positivas

## Que queda claro para auto-reddit

- `GET /api/scrape/new` SI sirve para candidate collection
- `GET /api/scrape_new_comments_and_its_post_content` SI sirve para thread context extraction
- `GET /api/scrape_post_comments` SI sirve como apoyo, contraste o fallback
- la integracion debe modelarse con la semantica real observada, no con el nombre idealizado del endpoint

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigacion.
