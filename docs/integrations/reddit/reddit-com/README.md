# reddit-com

**URL:** https://rapidapi.com/things4u-api4upro/api/reddit-com  
**Proveedor:** things4u-api4upro  
**Plataforma:** RapidAPI

---

## Resumen

API no oficial de Reddit descrita como "Real-time data, unofficial API reddit.com". Es la más opaca públicamente de las cuatro — solo se ha podido verificar un endpoint concreto.

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

## Autenticación

Vía RapidAPI (header `X-RapidAPI-Key`). Pendiente de verificar si requiere algo adicional.

---

## Endpoints relevantes

Catálogo no verificable públicamente. Único endpoint concreto verificado:

| Endpoint | Parámetros verificados | Descripción |
|---|---|---|
| `GET subreddit/awarding-totals` | `groupId` (ej: `t3_54z4f7`) | Awarding totals de un subreddit o post |

El resto del catálogo es desconocido. La descripción pública menciona datos "real-time" de Reddit, pero no se puede confirmar cobertura de posts o comentarios.

---

## Ejemplos de requests

```
GET https://reddit-com.p.rapidapi.com/subreddit/awarding-totals?groupId=t3_54z4f7
```

Pendiente de pruebas reales para el resto de endpoints.

---

## Ejemplos de responses

Pendiente de pruebas reales.

---

## Riesgos / dudas

- Documentación pública extremadamente escasa
- Solo un endpoint verificado, y no es el más relevante para el proyecto
- No se puede confirmar si cubre posts y comentarios de subreddits de forma útil
- Puede ser una API muy especializada o con cobertura limitada

---

## Encaje con auto-reddit

**Veredicto provisional: exploratoria / baja prioridad**

Con solo un endpoint verificado (`subreddit/awarding-totals`) que no es relevante para los casos de uso del proyecto, no hay base suficiente para considerarla como candidata principal o secundaria.

Solo considerarla si reddapi y reddit34 fallan en pruebas reales.

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
