# Diario del proyecto

---

## Entrada 1

**Fecha:** 25/03/2026

### Planteamiento inicial

El 25/03/2026 plantee a ChatGPT 5.4 una idea inicial bastante abierta: crear
un sistema para detectar dudas sobre Odoo y ERP en foros, especialmente
Reddit, y responderlas con ayuda de IA desde la cuenta de empresa de Halltic.

A partir de esa idea inicial, fui refinando el enfoque mediante varias
conversaciones centradas en producto, objetivos, riesgos, tono, casos de uso y
limites del sistema.

### Resultado de la primera fase

El resultado de esta primera fase fue pasar de la idea generica de "un bot
para responder en Reddit" a una definicion mucho mas concreta y realista: un
sistema que detecta oportunidades, filtra posts, genera respuestas sugeridas
con IA y las entrega al equipo para su publicacion manual.

Ese trabajo quedo consolidado en un documento de producto llamado
[Auto-Reddit](/docs/discovery/idea-inicial.md), que sirvio para dejar bien
definido el alcance funcional y preparar el analisis posterior de viabilidad
tecnica y arquitectura.

---

## Entrada 2

**Fecha:** 26/03/2026

### Product discovery formal

Usando la skill de product-discovery, se analizo `idea-inicial.md` con rigor
de producto. La primera conclusion fue clara: lo que habia definido no era un
unico cambio implementable, sino una **initiative** completa con varias
capacidades semindependientes (deteccion, filtrado, priorizacion, generacion y
entrega).

Se trabajo iterativamente para recortar el primer **slice vertical** del
producto: deteccion diaria de oportunidades en `r/Odoo` y entrega al equipo
de marketing y contenido por Telegram.

### Decisiones de producto cerradas

A lo largo de varias rondas de preguntas, se cerraron las reglas operativas
del primer slice:

- **Fuente v1:** `r/Odoo`.
- **Ventana temporal:** posts con creacion o actividad en los ultimos 7 dias.
- **Cola diaria:** los 20 posts no enviados mas recientes, ordenados por fecha
  de creacion.
- **Evaluacion IA:** la IA decide si un post merece respuesta, genera resumen
  y respuesta sugerida. Puede devolver `NO_SUGERIR` si no hay aportacion util.
- **Limite diario:** hasta 15 oportunidades enviadas.
- **Unicidad:** cada post solo se envia una vez. 3 estados posibles: `sent`,
  `approved` (pendiente para manana), `rejected`.
- **Hilo resuelto:** requiere dos senales de cierre salvo confirmacion
  explicita del autor.
- **Idioma:** la respuesta sugerida siempre en el idioma original del post.
- **Formato Telegram:** 1 mensaje resumen (fecha, posts revisados,
  oportunidades) + 1 mensaje por oportunidad (titulo, link, tipo, resumen
  post, resumen comentarios, respuesta sugerida).
- **Reglas editoriales:** no defender Odoo cuando sea objetivamente
  indefendible, Halltic visible solo si aporta contexto util, tono forero y
  tecnico, no hacer trabajo gratis en desarrollo.

El resultado se consolido en dos documentos separados:
- [`product.md`](/docs/product/product.md) — fuente de verdad del producto.
- [`ai-style.md`](/docs/product/ai-style.md) — comportamiento y estilo de la
  IA, separado del producto para no mezclar capas.

### Arquitectura fundacional

Se definieron las 8 decisiones arquitectonicas base del proyecto antes de
escribir una sola linea de codigo:

1. **Stack:** Python 3.14 + uv.
2. **Estructura:** monolito modular con contratos explicitos.
3. **Modelo operativo:** contenedor efimero + cron externo en VPS.
4. **Persistencia:** SQLite con modelo de 3 estados y TTL de 7 dias.
5. **Contratos:** Pydantic para comunicacion entre modulos.
6. **Configuracion:** pydantic-settings con `.env`, validacion al arrancar.
7. **Logging:** stdout, nivel minimo util (contadores + errores).
8. **Responsabilidades:** cada modulo tiene limites claros; ningun modulo
   importa a otro directamente, solo `shared/` y `config/`.

Documentado en [`architecture.md`](/docs/architecture.md).

### Descomposicion en changes (OpenSpec)

Se decidio dividir el proyecto en 5 changes verticales para implementacion
incremental via SDD (Spec-Driven Development):

1. `reddit-candidate-collection` — extraccion de candidatos desde Reddit.
2. `candidate-memory-and-uniqueness` — memoria operativa y control de
   duplicados.
3. `thread-context-extraction` — extraccion de contexto del post y
   comentarios.
4. `ai-opportunity-evaluation` — evaluacion IA de oportunidades.
5. `telegram-daily-delivery` — entrega diaria al equipo por Telegram.

Se creo la estructura OpenSpec en `openspec/changes/` con los 5 changes en
estado `identified`, sin proposals (esa fase la ejecutan subagentes
especializados).

### Scaffolding del proyecto

Se creo la estructura minima de codigo alineada con la arquitectura:

- `src/auto_reddit/` con 6 modulos: `reddit/`, `evaluation/`, `delivery/`,
  `persistence/`, `shared/`, `config/` y `main.py`.
- `tests/` con carpetas por modulo.
- `pyproject.toml` configurado para uv con hatchling.
- `Dockerfile` y `docker-compose.yml` para modelo efimero.
- `.env.example` con todas las variables.
- `.gitignore` completo.
- `config/settings.py` con pydantic-settings funcional.
- Dependencias instaladas y `uv.lock` generado.

### Skills del proyecto

Se crearon 3 skills especificas para el repositorio, registradas en
`AGENTS.md`:

- `python-conventions` — convenciones de codigo y arquitectura modular.
- `deepseek-integration` — patron de conexion con DeepSeek via SDK de OpenAI.
- `docker-deployment` — despliegue Docker con contenedor efimero.

### README

Se creo `README.md` en la raiz con descripcion general, stack tecnologico,
instrucciones de instalacion (pendientes de completar), estructura del proyecto
y funcionalidades principales.

### Resultado de la sesion

El proyecto paso de tener solo una idea general a tener:
- producto definido y documentado
- arquitectura cerrada
- scaffolding funcional
- planning preparado para implementacion incremental
- skills para guiar a los agentes de codigo

El siguiente paso es lanzar el primer change (`reddit-candidate-collection`)
con el subagente de proposals para empezar la cadena SDD.

---

## Entrada 3

**Fecha:** 27/03/2026

### Investigacion de APIs de Reddit

En esta sesion se paso de una idea abstracta de "usar APIs no oficiales" a una
investigacion tecnica y comparativa real sobre 4 APIs de RapidAPI:

- `reddapi`
- `reddit34`
- `reddit3`
- `reddit-com`

La validacion no se baso solo en documentacion publica. Tambien se hicieron
llamadas reales a endpoints para comprobar disponibilidad, shape de respuesta,
tiempos de respuesta y utilidad real para el caso de uso del proyecto:
detectar posts y comentarios recientes en `r/Odoo` dentro de los limites de las
cuotas gratuitas.

### Resultados tecnicos de la investigacion

La comparativa permitio bajar la discusion a comportamiento tecnico verificado
en vez de quedarse en promesas de catalogo:

- `reddapi` quedo bien documentada y demostro servir para posts nuevos y para
  recuperar contexto general del hilo, pero no devuelve comentarios realmente
  recientes aunque uno de sus endpoints lo sugiera por nombre.
- `reddit34` demostro ser la mejor candidata actual para comentarios recientes
  por post gracias a `getPostCommentsWithSort?sort=new`, con campos ricos como
  `id`, `created`, `permalink`, `depth` y `replies`.
- `reddit3` resulto ser mucho mas util de lo esperado: permite obtener posts
  nuevos, post + comentarios por URL y actividad reciente del subreddit
  mediante comentarios recientes.
- `reddit-com` quedo relegada a exploracion o busqueda global, porque devuelve
  demasiado ruido para el MVP.

### Decision estrategica provisional sobre APIs

A raiz de esta investigacion se cerro una estrategia de uso de APIs documentada
en [`docs/integrations/reddit/api-strategy.md`](/docs/integrations/reddit/api-strategy.md).

Las decisiones provisionales quedaron asi:

- **Posts nuevos de `r/Odoo`:** principal `reddit3`, fallback `reddapi`,
  segundo fallback `reddit34`.
- **Comentarios por post:** principal `reddit34`, fallback `reddit3`, segundo
  fallback `reddapi`.
- **`reddit-com`:** fuera del flujo principal.
- **Control operativo:** contador interno de cuota por API y deteccion de
  errores HTTP como mecanismo de control.
- **Reintentos:** 2 retries con backoff de 2s y 4s.
- **Fallo total:** si todas las APIs fallan, el sistema no envia nada y lo
  reintenta al dia siguiente.

### Replanteamiento de limites operativos del producto

Al analizar las cuotas gratuitas reales, se detecto que el diseno original era
demasiado agresivo para el volumen disponible. Por eso se reviso el producto
para adaptarlo a una operativa realista en gratuito:

- ejecutar solo de lunes a viernes
- revisar 10 posts al dia
- enviar como maximo 10 oportunidades al dia

Estos valores quedan como provisionales y revisables cuando haya uso real y se
pueda medir cobertura, estabilidad y consumo efectivo.

### Documentacion generada o actualizada

Esta fase no solo sirvio para decidir, sino tambien para dejar trazabilidad
util. Entre los documentos mas relevantes creados o actualizados estan:

- `docs/integrations/reddit/comparison.md`
- `docs/integrations/reddit/api-strategy.md`
- `docs/integrations/reddit/reddapi/README.md`
- `docs/integrations/reddit/reddit34/README.md`
- `docs/integrations/reddit/reddit3/README.md`
- `docs/integrations/reddit/reddit-com/README.md`
- `README.md`
- `docs/architecture.md`

### Resultado de la sesion

El proyecto ya no solo tiene producto, arquitectura y scaffolding. Ahora
tambien tiene una estrategia concreta y documentada para el uso realista de las
APIs de Reddit dentro de los limites de sus cuotas gratuitas.

---

## Entrada 4

**Fecha:** 27/03/2026

### Alineacion documental con decisiones cerradas del discovery

Se hizo una pasada de consolidacion para alinear la documentacion viva del repo
con las decisiones ya cerradas del discovery y evitar contradicciones entre
documentos operativos, historicos y de planificacion.

### Decisiones reafirmadas como fuente de verdad

- `reddit-candidate-collection` recoge SOLO posts de `r/Odoo`.
- La ventana temporal se calcula por `created_at` dentro de los ultimos 7 dias.
- La priorizacion operativa es por posts mas recientes.
- La coleccion inicial NO incluye comentarios.
- `thread-context-extraction` recupera comentarios SOLO para los posts
  seleccionados aguas arriba.
- Se procesan como maximo 10 posts por ejecucion diaria para el flujo
  posterior.
- El caso `post antiguo pero vivo` queda fuera del alcance actual.
- No existe backlog explicito ni estado `approved`.
- Si un post no se envia hoy pero sigue dentro de los 7 dias y no esta marcado
  como enviado, manana vuelve a competir normalmente desde la ventana.

### Documentacion afectada

Se actualizaron como documentos vivos:

- `docs/integrations/reddit/api-strategy.md`
- `docs/product/product.md`
- `docs/architecture.md`
- `README.md`
- `docs/README.md`
- documentacion comparativa y READMEs tecnicos de APIs bajo
  `docs/integrations/reddit/`

Y se mantuvieron como historicos con avisos de supersesion:

- `docs/discovery/idea-inicial.md`
- `docs/discovery/ideas.md`

### Resultado

Queda explicitado que el sistema actual trabaja con un modelo 10/10, ventana de
7 dias por fecha de creacion, sin backlog editorial persistente y con
comentarios recuperados solo despues de la seleccion aguas arriba.

---

## Entrada 5

**Fecha:** 27/03/2026

### Cierre del discovery del change 1

Se cerro formalmente el discovery de `reddit-candidate-collection` y se dejo
trazado en `openspec/discovery/reddit-candidate-collection.md`.

### Alcance confirmado

- El change 1 recoge todos los posts de `r/Odoo` creados en los ultimos 7 dias.
- En esta fase no se recuperan comentarios; la salida se entrega normalizada en
  memoria/proceso.
- Los posts incompletos no se descartan: se conservan marcados como
  incompletos.

### Relacion con cambios posteriores

- El change 2 excluye `sent` y `rejected`, selecciona 10 candidatos por
  recencia y no usa estado `approved`.
- `not selected today` no equivale a `rejected`; el post vuelve a competir si
  sigue dentro de la ventana.
- Si Telegram falla despues de una aceptacion de IA, se reintenta el envio sin
  reevaluar la IA.

### Gap abierto

Queda pendiente decidir la estrategia exacta de paginacion o batching para
recorrer toda la ventana real de 7 dias cuando se hagan pruebas contra los
endpoints de Reddit.

---

## Entrada 6

**Fecha:** 27/03/2026

### Revalidacion tecnica del change 1

Antes de pasar a `sdd-tasks`, se cerro una ronda adicional de evidencia tecnica
para confirmar que la estrategia del change 1 aguanta en condiciones reales de
cuota y de integracion con RapidAPI.

### Ajustes y validaciones cerradas

- Se bajo el cap operativo downstream de 10 a 8 por tension real de cuotas: el
  happy path queda en unas 198 requests/mes y deja alrededor de 22 requests/mes
  de margen sobre unas 220 utiles actuales.
- Se creo y ejecuto `scripts/reddit_api_raw_snapshot.py` para generar raws JSON
  directos de las APIs y dejar evidencia reproducible.
- Durante esa captura se detecto un bug con `reddapi`: Cloudflare bloqueaba la
  firma por defecto y se corrigio usando `User-Agent: RapidAPI Playground`.
- Con los raws reanalizados, se revalido la estrategia operativa: posts por
  `reddit3 -> reddit34 -> reddapi`; comentarios por `reddit34 -> reddit3 ->
  reddapi`, dejando `reddapi` como fallback degradado para comentarios.
- Tambien se redacto el design de `reddit-candidate-collection` en
  `openspec/changes/reddit-candidate-collection/design.md`, revisando tanto los
  artefactos del change como la documentacion viva y la evidencia raw.

### Resultado

El change 1 queda mejor aterrizado para entrar en `sdd-tasks`: ya no solo hay
direccion funcional, sino tambien evidencia tecnica reciente, ajuste de
capacidad y un design apoyado en pruebas reales.
