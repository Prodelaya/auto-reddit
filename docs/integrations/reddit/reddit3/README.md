# reddit3

**URL:** https://rapidapi.com/sparior/api/reddit3  
**Proveedor:** sparior  
**Plataforma:** RapidAPI

---

## Resumen

API no oficial de Reddit. Parece cubrir recuperación de contenido de Reddit incluyendo posts y búsqueda. La documentación pública es muy escasa — gran parte del catálogo de endpoints no está indexado.

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

Información muy limitada. Lo verificable públicamente:
- Al menos un endpoint basado en query param `url` relacionado con comentarios/contenido de un hilo
- Indicios de cobertura de posts y búsqueda

Catálogo completo: **no verificable públicamente**.

---

## Ejemplos de requests

Pendiente de pruebas reales.

---

## Ejemplos de responses

Pendiente de pruebas reales.

---

## Riesgos / dudas

- Documentación pública muy escasa
- No se pueden verificar endpoints concretos sin acceso al playground
- Desconocida la cobertura real para posts y comentarios de subreddits
- Plan gratuito insuficiente para uso real

---

## Encaje con auto-reddit

**Veredicto provisional: exploratoria / baja prioridad**

No hay suficiente información pública para confirmar que cubre los dos casos de uso clave del proyecto:
1. traer posts de `r/Odoo` ordenados por fecha de creación
2. traer comentarios de un post concreto

Pendiente de validar con pruebas reales antes de considerar como candidata.

---

> `raw/` contiene material sin procesar: capturas, JSONs de prueba y notas de investigación.
