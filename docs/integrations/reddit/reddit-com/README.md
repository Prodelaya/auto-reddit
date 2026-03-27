# reddit-com

**URL:** https://rapidapi.com/things4u-api4upro/api/reddit-com  
**Proveedor:** things4u-api4upro  
**Plataforma:** RapidAPI

---

## Resumen

API no oficial de Reddit en RapidAPI (`reddit-com`). Antes solo se habia verificado un endpoint aislado poco util (`subreddit/awarding-totals`).

La prueba real util de esta ronda confirma que la API expone al menos un endpoint de busqueda global por texto con respuesta rica, pero NO orientada de forma directa a collection por subreddit especifico.

---

## Plan gratuito

| Concepto | Límite |
|---|---|
| Requests/mes | 100 (hard limit) |
| Rate limit | 1000 req/hora |
| Bandwidth | 10240 MB/mes |
| Coste extra | +$0.001 por 1 MB adicional |

**Estimacion de viabilidad:** con ~21 requests/dia de consumo estimado, el plan gratuito dura aproximadamente **5 dias**. No viable para uso real continuo.

---

## Autenticacion

Via RapidAPI (header `X-RapidAPI-Key`). No se documenta aqui ningun requisito adicional verificado.

---

## Endpoint probado

Endpoint probado en esta ronda:

`GET https://reddit-com.p.rapidapi.com/posts/search-posts?query=odoo&sort=new&time=week`

Resultados observados en pruebas reales:

- `200 OK`
- ~3200 ms en una prueba y ~2861 ms en otra
- Shape real con `data`, `status`, `message`, `meta.nextPage`
- Cada post trae campos ricos como `id`, `createdAt`, `postTitle`, `url`, `content` (cuando aplica), `commentCount`, `authorInfo`, `subreddit.prefixedName`, `permalink`, `outboundLink`
- El endpoint devuelve resultados globales por texto, no resultados limitados a `r/Odoo`
- La respuesta incluye mucho ruido: `r/stealabrainrot`, `r/UAEjobseekers`, `r/webdesign`, `r/Panama`, `r/ERP_CRM_Peru`, `r/Cleverence`, etc.
- Si aparecen posts de `r/Odoo`, pero mezclados con muchos no relevantes

---

## Que aporta realmente

Es una API de busqueda global bastante rica a nivel de shape.

Lo util que si queda verificado:

- Puede recuperar posts recientes relacionados con una query textual
- Devuelve bastante contexto por item, lo que facilita analisis posterior o features de exploracion
- Tiene potencial para una feature futura de exploracion o busqueda global sobre Reddit

---

## Riesgos / dudas

- La documentacion publica sigue siendo escasa
- La prueba valida busqueda global por query, pero no confirma una via directa y limpia para recuperar solo `r/Odoo`
- Para el caso del MVP obliga a filtrar demasiado ruido
- Sigue sin quedar verificado un flujo subreddit-specific comparable a `reddit34` o `reddit3`

---

## Encaje con auto-reddit

**Veredicto provisional: exploratoria / util para busqueda global, poco adecuada para el MVP actual**

No sirve bien como fuente principal de candidate collection para el MVP porque no recupera directamente `r/Odoo`, sino posts que mencionan o contienen `odoo` en cualquier subreddit.

Para el flujo principal actual queda por detras de `reddit34` y `reddit3`, que ya cubren mejor la captura de posts y comentarios relevantes con menos ruido.

Puede tener valor futuro para exploracion o busqueda global, pero no para el flujo principal actual.

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
