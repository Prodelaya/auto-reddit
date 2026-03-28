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

---

## Entrada 7

**Fecha:** 27/03/2026

### SDD apply del change 1: implementacion real

Se ejecuto el ciclo completo de apply para `reddit-candidate-collection`. El
change paso de tener spec, design y tasks a tener codigo funcional real.

### Lo que se implemento

- `src/auto_reddit/shared/contracts.py`: modelo `RedditCandidate` con todos los
  campos del contrato minimo y el campo computado `is_complete`, que marca
  candidatos incompletos sin descartarlos.
- `src/auto_reddit/reddit/client.py`: cliente completo con tres normalizers
  independientes por provider (`reddit3`, `reddit34`, `reddapi`), helper
  `_to_absolute_url` para canonizar URLs relativas, extractores de cursor
  separados por provider, funcion `_fetch_with_retry` con backoff exponencial
  (2s, 4s), bucle de paginacion generico `_paginate` y punto de entrada publico
  `collect_candidates` con fallback chain `reddit3 → reddit34 → reddapi`.
- `src/auto_reddit/main.py`: funcion `run()` que llama `collect_candidates` y
  deja placeholders comentados para los changes siguientes.
- `tests/test_reddit/`: 50 tests con fixtures de raws reales (sanitizados) de
  los tres providers, cubriendo normalizacion, filtrado temporal, filtrado por
  subreddit, paginacion, fallback chain, reintentos e `is_complete`.

### Decisiones tecnicas cerradas durante el apply

- Los candidatos incompletos se conservan con `is_complete=False`; no se
  descartan. La decision de que hacer con ellos es del paso siguiente.
- `url` y `permalink` se canonican a URL absoluta en el normalizer, no en el
  consumidor.
- El filtro de subreddit se aplica post-normalizacion con
  `subreddit.lower() == "odoo"` como guard explicito.
- El fallback chain es whole-step: si un provider falla en cualquier punto se
  descarta entero y se intenta el siguiente.
- `User-Agent: RapidAPI Playground` es obligatorio para `reddapi`; sin el,
  Cloudflare devuelve 403.
- La incognita sobre la ubicacion del cursor por provider quedo resuelta
  verificando los raws: `reddit3` en `meta.cursor`, `reddit34` en
  `data.cursor`, `reddapi` en `cursor` raiz.

### Resultado

21 tasks completadas, 50 tests pasando. El change 1 listo para verificacion.

---

## Entrada 8

**Fecha:** 27/03/2026

### Verificacion y archivo del change 1

Se ejecuto el ciclo de verify para `reddit-candidate-collection`. El primer
verify detecto gaps de cumplimiento reales:

- `is_complete` no validaba todos los campos minimos del contrato.
- Faltaba filtro explicito de subreddit post-normalizacion.
- `url` no se canonizaba, solo `permalink`.

Se hizo un apply correctivo que cerro los tres gaps. El segundo verify dio
PASS: 21/21 tasks completas, 50 tests pasando, 6 escenarios de spec cubiertos.

El change quedo archivado formalmente:

- artefactos movidos a
  `openspec/changes/archive/2026-03-27-reddit-candidate-collection/`
- spec promovida a `openspec/specs/reddit-candidate-collection/spec.md` como
  fuente de verdad permanente
- archive report guardado en OpenSpec y Engram

### Modelo DeepSeek recomendado

En paralelo se actualizo `docs/product/ai-style.md` para recomendar
oficialmente `deepseek-chat` (DeepSeek-V3) en lugar de `deepseek-reasoner`
(R1). La razon: el pipeline necesita clasificacion NLP, estructura JSON estricta
(Pydantic) y tono breve y pragmatico. Los modelos reasoning sobreexplican,
violan el tono editorial y resultan mas lentos y costosos para este caso de uso.

---

## Entrada 9

**Fecha:** 27/03/2026

### Guia didactica TFM

Se creo `TFM/guia-didactica-auto-reddit.md`, un documento unico que actua como
guia de aprendizaje para juniors usando el proyecto como hilo conductor.

La guia no es un manual de onboarding al proyecto. Su objetivo es que alguien
que empiece a leerla sin conocer el repo entienda por que se toman decisiones
de arquitectura, que son los contratos, como funciona el desarrollo asistido por
IA con disciplina y como esta construido este sistema concretamente.

Contiene: overview, project map, glosario, arquitectura explicada para juniors,
decisiones con trade-offs, explicacion de OpenSpec/SDD/skills/AGENTS/GitNexus/
Engram/MCP, recorrido por carpetas y archivos Python, flujos del sistema,
riesgos y mitigaciones, learning notes e historial de changes archivados.

La guia es un documento vivo: se actualiza con cada change archivado.

---

## Entrada 10

**Fecha:** 27/03/2026 — 28/03/2026

### SDD completo del change 2: memoria operativa y unicidad

Se ejecuto el ciclo SDD completo para `candidate-memory-and-uniqueness`:
discovery, proposal, spec, design, tasks, apply, verify y archive.

### Problema que resuelve

Sin memoria operativa, el pipeline enviaria por Telegram los mismos posts cada
dia. Tampoco habria forma de reintentar una entrega fallida sin volver a llamar
a la IA, lo que consume cuota y puede cambiar el resultado.

### Lo que se implemento

- `src/auto_reddit/shared/contracts.py`: enum `PostDecision` (`sent`,
  `rejected`, `pending_delivery`) y modelo `PostRecord` con `opportunity_data`
  para reintentos sin re-evaluar la IA.
- `src/auto_reddit/persistence/store.py`: clase `CandidateStore` con SQLite.
  Operaciones: `init_db`, `get_decided_post_ids`, `save_rejected`,
  `save_pending_delivery`, `mark_sent`, `get_pending_deliveries`. Todos los
  writes usan upsert (`INSERT ... ON CONFLICT DO UPDATE`).
- `src/auto_reddit/main.py`: integracion del store — inicializacion, exclusion
  de decididos, recorte a 8, placeholders comentados para changes 3, 4 y 5.
- `src/auto_reddit/config/settings.py`: campo `db_path` para la ruta del
  fichero SQLite.
- `tests/test_persistence/test_store.py`: 20 tests unitarios.

### Decisiones tecnicas clave

- `get_decided_post_ids` devuelve `sent` y `rejected` pero NO
  `pending_delivery`. Un post en `pending_delivery` sigue siendo elegible para
  reintento Telegram sin re-evaluar la IA.
- El estado transitorio se llama `pending_delivery`, no `approved`. El nombre
  comunica la semantica exacta: la IA acepto, Telegram aun no ha confirmado.
- `opportunity_data` guarda el JSON del resultado IA para poder reintentar sin
  volver a llamar al modelo.

### Verificacion

PASS CON ADVERTENCIAS — 16/16 tasks completas, 70 tests pasando. Advertencias
no bloqueantes preservadas en el archive:

- no existe test que pruebe "skipped today, eligible tomorrow" en dos runs
  consecutivos.
- no existe test end-to-end de reintento Telegram usando `pending_delivery` sin
  re-llamar a la IA.

Ambas son pruebas de integracion entre runs que requieren un enfoque diferente
al unitario. Quedan pendientes.

### Archive

- artefactos en
  `openspec/changes/archive/2026-03-27-candidate-memory-and-uniqueness/`
- spec promovida a `openspec/specs/candidate-memory/spec.md`
- 70 tests pasando en total (50 change 1 + 20 change 2)

---

## Entrada 11

**Fecha:** 28/03/2026

### SDD completo del change 3: extraccion de contexto de hilo

Se ejecuto el ciclo SDD completo para `thread-context-extraction`: discovery,
proposal, spec, design, tasks, apply, verify y archive.

### Problema que resuelve

La IA necesita contexto real del hilo para evaluar si merece intervencion: el
titulo y el selftext solos no son suficientes. Este change enriquece solo los
posts ya seleccionados aguas arriba con el arbol de comentarios normalizado,
sin mezclar esa extraccion con la evaluacion IA ni con la entrega.

### Lo que se implemento

- `src/auto_reddit/shared/contracts.py`: tres nuevos contratos:
  - `ContextQuality` enum (`full`, `partial`, `degraded`) para indicar la
    calidad del contexto segun el proveedor que respondio.
  - `RedditComment` modelo con campos opcionales cuando el proveedor no los
    expone (`comment_id`, `created_utc`, `permalink`, `parent_id`, `depth`
    son `None` para reddapi).
  - `ThreadContext` modelo que empaqueta el candidato original, la lista de
    comentarios normalizados, el conteo, la calidad y el proveedor usado.
- `src/auto_reddit/reddit/comments.py`: modulo nuevo con funcion publica
  `fetch_thread_contexts` que recibe el review set y devuelve un dict
  `post_id → ThreadContext`. Internamente tiene normalizers por proveedor y
  fallback chain `reddit34 → reddit3 → reddapi`.
- `src/auto_reddit/main.py`: `fetch_thread_contexts` conectado como change 3,
  placeholder de change 4 actualizado con la variable `thread_contexts`.
- `tests/test_reddit/test_comments.py`: 37 tests nuevos (total 107 en suite).

### Hallazgo tecnico importante: reddit3 y la metadatos de anidamiento

Durante el apply se detecto que los raws de reddit3 no incluyen `parent_id`
ni `depth` como campos directos. El arbol se puede recorrer recursivamente
via `replies[]`, pero derivar `depth` sintetico desde la posicion del arbol
no es equivalente a un `depth` real del API.

Decision: el normalizer de reddit3 deja `depth=None` y `parent_id=None` para
todos los comentarios. Esto se refleja en `ContextQuality.partial` cuando
reddit3 actua como proveedor. Los artefactos de design y tasks se alinearon
con esta realidad durante la fase de apply.

### Calidad de contexto por proveedor

| Proveedor | Calidad | Razon |
|---|---|---|
| reddit34 | `full` | Arbol de replies, timestamps ISO 8601, sort=new garantizado |
| reddit3  | `partial` | Lista recursiva completa, sin `depth`/`parent_id` |
| reddapi  | `degraded` | Solo top comments, plano, sin `comment_id` ni timestamps |

### Detalle tecnico: datetime de reddit34

reddit34 devuelve el campo `created` de comentarios en formato ISO 8601
(`"2026-03-27T13:46:04.000000+0000"`), no como unix timestamp. El normalizer
aplica `fromisoformat()` con sustitucion `+0000` → `+00:00` para compatibilidad
con Python antes de convertir a int.

### Verificacion

PASS — 14/14 tasks completas, 107 tests pasando, 7/7 escenarios de spec
cubiertos. El primer verify detecto una discrepancia de wording en los
artefactos sobre reddit3 y `depth`; se resolvio alineando design y tasks con
la implementacion real (sin cambiar codigo) y el verify final quedo en PASS
limpio.

### Archive

- artefactos en
  `openspec/changes/archive/2026-03-28-thread-context-extraction/`
- spec promovida a `openspec/specs/thread-context-extraction/spec.md`
- 107 tests pasando en total (50 change 1 + 20 change 2 + 37 change 3)

---

## Entrada 12

**Fecha:** 28/03/2026

### SDD completo del change 4: evaluacion IA de oportunidades

Se ejecuto el ciclo SDD completo para `ai-opportunity-evaluation`: discovery,
proposal, spec, design, tasks, apply, verify (con ciclo correctivo) y archive.

### Problema que resuelve

El equipo humano necesita que la IA ya haya prefiltrado y valorado cada post
antes de recibirlo por Telegram. Sin este change, el sistema entrega candidatos
en bruto; con el, entrega decisiones justificadas con resumen, tipo de
oportunidad, respuesta sugerida en dos idiomas y, cuando aplica, senales de
revision critica para el humano.

### Refinamiento del diseno con feedback de analistas externos

Antes de lanzar el apply, el diseno del system prompt se reviso con feedback
de analistas. Las decisiones mas relevantes adoptadas:

- estructura de dos fases obligatoria en el prompt: DECIDE primero, GENERA
  despues; impide que la IA racionalice la aceptacion retroactivamente
- campo `opportunity_reason`: la IA debe explicar POR QUE su intervencion
  aporta valor, no solo resumir el post
- campo `comment_summary_es` nullable: no forzar resumen cuando no hay
  comentarios utiles
- guardrail anti-Halltic: Halltic solo se menciona si el hilo busca
  explicitamente un partner y la mencion aporta contexto real
- limitacion de longitud de respuesta: entre 2 y 6 frases, tono forero y
  pragmatico

### Lo que se implemento

- `src/auto_reddit/shared/contracts.py`: seis nuevos contratos:
  - `OpportunityType` enum: `funcionalidad`, `desarrollo`,
    `dudas_si_merece_la_pena`, `comparativas`
  - `RejectionType` enum: `resolved_or_closed`, `no_useful_contribution`,
    `excluded_topic`, `insufficient_evidence`
  - `AIRawResponse`: validacion Pydantic de la respuesta JSON de DeepSeek
  - `AcceptedOpportunity`: combina campos deterministicos del pipeline con
    campos generados por la IA; `model_dump_json()` produce el JSON listo
    para persistir en `opportunity_data`
  - `RejectedPost`: post rechazado con tipo de rechazo explicito
  - `EvaluationResult`: union discriminada `AcceptedOpportunity | RejectedPost`
- `src/auto_reddit/evaluation/evaluator.py`: evaluador completo con system
  prompt estatico cacheable, constructor de mensaje de usuario deterministico,
  retry con tenacity (backoff exponencial), validacion Pydantic de respuesta,
  y funcion publica `evaluate_batch` que orquesta la evaluacion de un dict
  `post_id → ThreadContext`
- `src/auto_reddit/evaluation/__init__.py`: expone `evaluate_batch`
- `src/auto_reddit/main.py`: change 4 conectado — llama `evaluate_batch`,
  persiste `AcceptedOpportunity` como `pending_delivery` y `RejectedPost`
  como `rejected`, logea aceptados/rechazados/saltados
- `tests/test_evaluation/`: 56 tests nuevos en dos ficheros (contracts y
  evaluator), total 163 tests en suite

### Decisiones tecnicas clave

- **Dos fases en el prompt**: el modelo primero decide (acepta/rechaza) y
  despues genera contenido. Esta estructura evita la racionalizacion post-hoc
  y mejora la precision de la decision.
- **Campos deterministicos fuera de la IA**: `post_id`, `title` y `link`
  los construye el pipeline; la IA no los genera. Solo genera lo que requiere
  razonamiento: tipo, razon, resumenes, respuesta y deteccion de idioma.
- **`warning`/`human_review_bullets` solo en aceptaciones con contexto
  degradado**: si la IA rechaza, no tiene sentido enviar senales de revision
  humana. Los posts rechazados solo llevan `rejection_type`.
- **Retry/skip semantics**: si un post falla todos los reintentos, se salta
  ese post y se continua con el siguiente; no se aborta el batch.
- **`opportunity_data` como fuente de reintento**: `AcceptedOpportunity`
  serializado en JSON queda en `store.save_pending_delivery`; el change 5
  puede reintentar Telegram usando ese JSON sin volver a llamar a la IA.
- **Sistema de tipos cerrado**: `OpportunityType` y `RejectionType` son enums;
  cualquier valor fuera del esquema falla la validacion Pydantic antes de
  llegar al resto del pipeline.

### Ciclo correctivo post-verify

El primer verify detecto dos gaps criticos:

1. Los `RejectedPost` en contexto degradado propagaban `warning` y
   `human_review_bullets` aunque la spec los reserva para aceptaciones.
2. Faltaba evidencia de runtime del path `partial` (reddit3 como proveedor
   de comentarios).

Resolucion: apply correctivo que (1) descarta `warning`/`bullets` en
`RejectedPost` y (2) anade tests explicitamente para el path `partial`.
El verify final dio PASS CON ADVERTENCIAS de baja severidad.

### Verificacion

PASS CON ADVERTENCIAS — 37/37 tasks completas, 163 tests pasando. Advertencias
no bloqueantes preservadas:

- la prueba de handoff upstream es parcial (sin test end-to-end de integracion
  entre evaluate_batch y el resto del pipeline)
- la reutilizacion de `opportunity_data` para reintento Telegram solo esta
  probada parcialmente a nivel runtime
- no hay build/type-check configurado (por reglas del proyecto)

### Archive

- artefactos en
  `openspec/changes/archive/2026-03-28-ai-opportunity-evaluation/`
- spec promovida a `openspec/specs/ai-opportunity-evaluation/spec.md`
- spec de `candidate-memory` actualizada para reflejar el modelo de
  `opportunity_data` como fuente de reintento
- 163 tests pasando en total (50 + 20 + 37 + 56)

---

## Entrada 13

**Fecha:** 28/03/2026

### SDD completo del change 5: entrega diaria por Telegram

Se ejecuto el ciclo SDD completo para `telegram-daily-delivery`: discovery,
proposal, spec, design, tasks, apply, verify (con ciclo correctivo) y archive.
Es el ultimo change del pipeline principal.

### Problema que resuelve

Los resultados de la evaluacion IA quedan persistidos en SQLite como
`pending_delivery`. Sin este change, nunca llegarian al equipo humano. Este
change cierra el circuito: selecciona los registros pendientes, los formatea
como mensajes Telegram en HTML y los entrega con retry semantico, enviando
el `sent` a la base de datos solo tras confirmacion de entrega.

### Arquitectura del modulo de delivery

Se creo el modulo `delivery/` con tres colaboradores separados por
responsabilidad, mas el orquestador publico:

- `delivery/selector.py`: seleccion deterministica del set diario a partir de
  los registros `pending_delivery` en SQLite. Aplica TTL (7 dias desde
  `decided_at`), ordena reintentos antes que nuevos dentro del cap, y excluye
  registros con `opportunity_data` malformed antes de gastar el cap.
- `delivery/renderer.py`: renderizado deterministico de mensajes Telegram en
  HTML. `render_opportunity` formatea un mensaje por oportunidad;
  `render_summary` genera el mensaje de resumen diario con fecha, posts
  revisados y conteo de oportunidades (campos exigidos por `product.md §10`).
- `delivery/telegram.py`: cliente minimo de la Bot API de Telegram.
  `send_message` hace una llamada HTTP POST y devuelve `bool`. Sin logica de
  negocio: solo transporte.
- `delivery/__init__.py`: `deliver_daily` como punto de entrada unico. Orquesta
  selector, renderer y cliente; marca `sent` en SQLite solo tras confirmacion;
  envia el resumen de forma no bloqueante (fallo del resumen no aborta
  entregas individuales); purga registros expirados al final.

### Contratos nuevos

- `DeliveryReport` en `shared/contracts.py`: informe de una ejecucion de
  entrega con campos `total_selected`, `retries`, `new`, `sent_ok`,
  `sent_failed`, `summary_sent`, `expired_skipped`.
- `CandidateStore.purge_expired(post_ids)` en `persistence/store.py`: elimina
  registros `pending_delivery` con TTL expirado; llamado por `deliver_daily`
  al final del ciclo.

### Integracion en `main.py`

El change 5 cierra el pipeline:

```python
report = deliver_daily(store, settings, reviewed_post_count=len(review_set))
```

El parametro `reviewed_post_count` viene del tramo upstream para que el
resumen de Telegram informe cuantos posts se revisaron ese dia, tal como
exige el documento de producto.

### Ciclo correctivo post-verify

El primer verify detecto tres issues reales:

1. El selector consumia cap con registros de `opportunity_data` malformed; los
   registros invalidos deberian excluirse antes de entrar en el recuento.
2. `render_summary` no incluia fecha ni conteo de posts revisados, campos
   exigidos explicitamente en `product.md §10`.
3. `purge_expired` no estaba implementado; el metodo existia pero el cuerpo
   era un `pass`.

Los tres se corrigieron en el apply correctivo. El verify final dio PASS.

### Decisiones tecnicas clave

- **Retry-first dentro del cap**: los reintentos (registros ya con intento
  previo fallido) tienen prioridad sobre registros nuevos. Maximiza la
  probabilidad de que una oportunidad ya evaluada llegue al equipo aunque
  Telegram haya fallado ayer.
- **`sent` solo tras confirmacion**: el estado `sent` no se escribe hasta que
  Telegram confirma la entrega. Un fallo de red entre evaluacion y entrega no
  produce un post marcado como enviado sin haberlo entregado.
- **Resumen no bloqueante**: si el mensaje de resumen falla, las entregas
  individuales ya estan enviadas. El sistema no deshace lo entregado por un
  fallo de un mensaje de menor criticidad.
- **TTL de 7 dias**: un registro `pending_delivery` que no se haya podido
  entregar en 7 dias se descarta; despues de esa ventana el post ya no es
  relevante editorialmente.
- **Separation of concerns estricta**: selector no sabe de Telegram; renderer
  no sabe de SQLite; cliente no sabe del negocio. `deliver_daily` los conecta.

### Verificacion

PASS CON ADVERTENCIAS — 18/18 tasks completas, 259 tests pasando. Advertencias
no bloqueantes preservadas:

- no existe test de orquestacion que pruebe que la entrega nunca re-entra en
  la evaluacion IA ni en paths de publicacion directa en Reddit
- no hay build/type-check configurado (por reglas del proyecto)

### Archive

- artefactos en
  `openspec/changes/archive/2026-03-28-telegram-daily-delivery/`
- spec promovida a `openspec/specs/telegram-daily-delivery/spec.md`
- 259 tests pasando en total (50 + 20 + 37 + 56 + 96)
- **Pipeline completo**: los cinco changes del proyecto estan archivados

---

## Entrada 14

**Fecha:** 28/03/2026

### SDD completo del change 6: tests de integracion operacional

Se ejecuto el ciclo SDD completo para `operational-integration-tests`:
discovery, proposal, spec, design, tasks, apply, verify (con ciclo correctivo
de alineacion de artefactos) y archive.

### Por que este change existe

Al cerrar los cinco changes funcionales, las advertencias de verify de los
changes 4 y 5 senalaban el mismo gap: no existia ningun test que probase el
comportamiento del pipeline como orquestador. Los tests unitarios cubren cada
modulo por separado, pero nadie verificaba que:

- el reintento de Telegram usa el resultado persistido de la IA y no la
  vuelve a llamar
- la fase de delivery no re-entra en la evaluacion IA ni en paths de
  publicacion directa en Reddit
- la evaluacion no produce side effects en la entrega
- entre dos ejecuciones consecutivas, los posts decididos en la primera
  quedan correctamente excluidos en la segunda

Este change cierra esas brechas sin anadir funcionalidad nueva. Solo tests.

### Lo que se implemento

`tests/test_integration/test_operational.py`: 832 lineas, 10 tests en 4
clases, 1 smoke test optional:

- `TestRetryWithoutAIReEvaluation`: prueba que un `pending_delivery`
  persiste entre ejecuciones y que el reintento de Telegram no llama a
  `evaluate_batch` ni a los providers de Reddit.
  - `test_retry_uses_persisted_data_without_ai_call`
  - `test_retry_does_not_call_evaluate_batch_even_if_new_candidates_zero`

- `TestDeliveryBoundaryIsolation`: prueba que la fase de delivery solo
  consume registros persistidos; nunca re-entra en coleccion de candidatos
  ni en evaluacion IA.
  - `test_delivery_reads_only_persisted_records_no_upstream_reentry`

- `TestEvaluationBoundaryIsolation`: prueba que la evaluacion no produce
  side effects en la entrega; que una aceptacion queda persistida antes de
  que llegue al modulo de delivery; que un rechazo no llama al cliente
  Telegram.
  - `test_evaluation_boundary_no_delivery_side_effect_on_rejection`
  - `test_evaluation_accepted_outcome_persisted_before_delivery_phase`
  - `test_rejected_post_stored_without_delivery_side_effect`

- `TestMultiRunMemoryBoundaries`: prueba el comportamiento entre dos runs
  consecutivos con SQLite real (no mock): sent y rejected de la primera
  ejecucion quedan excluidos en la segunda; `pending_delivery` se reintenta
  sin re-evaluar la IA en la segunda ejecucion.
  - `test_run1_persists_sent_and_rejected_correctly`
  - `test_run2_excludes_sent_and_rejected_processes_new`
  - `test_pending_delivery_retry_excluded_from_decided_set`
  - `test_pending_delivery_retried_without_ai_call_in_run2`

- `TestRedditSmokeOptional` (1 test, opcional):
  - `test_real_reddit_collect_candidates_returns_nonempty_list`: solo se
    ejecuta si existe la variable de entorno `REDDIT_SMOKE_API_KEY`. Hace
    una llamada real a Reddit y verifica que devuelve al menos un candidato.
    No forma parte de los criterios de pass/fail del verify normal.

### Decisiones tecnicas de diseno de tests

- **SQLite real con `tmp_path`**: `TestMultiRunMemoryBoundaries` usa un
  fichero SQLite temporal real, no un mock. Esto es lo que hace que el test
  sea util: prueba la persistencia real, no una simulacion.
- **Parche en el namespace del caller**: los patches de `evaluate_batch` y
  `send_message` se aplican en `auto_reddit.main`, no en el modulo donde
  estan definidos. Es como Python resuelve los nombres en tiempo de
  ejecucion.
- **Sentinel estricto para isolation tests**: para probar que una fase no
  llama a otra, se usa un sentinel que levanta `AssertionError` si es
  invocado; si el test pasa, la fase no fue llamada.
- **Env-gated para smoke**: `@pytest.mark.skipif(not os.getenv(...))` mantiene
  el smoke test fuera del CI sin necesidad de configuracion especial.

### Ciclo correctivo

El primer verify detecto un mismatch de wording: la spec y las tasks
describian el proof de P2 (boundary de delivery) como "sentinels que fallan
si se llaman", pero la implementacion real usa entrada controlada vacia que
atraviesa `main.run()` sin llamar a los modulos upstream. No habia que
cambiar codigo: solo alinear el wording de spec, design, tasks y verify con
la estrategia de prueba real. El verify final dio PASS limpio.

### Resultado

PASS — 10/10 tasks completas. Suite completa: 269 tests pasando, 1 skipped
(el smoke test opcional). Sin advertencias de baja severidad ni sugerencias
pendientes — este change cierra las brechas abiertas en los changes 4 y 5.

### Archive

- artefactos en
  `openspec/changes/archive/2026-03-28-operational-integration-tests/`
- spec promovida a `openspec/specs/operational-integration-tests/spec.md`
- 269 tests pasando + 1 skipped (50 + 20 + 37 + 56 + 96 + 10)
- **Cobertura completa**: unitaria + integracion operacional archivadas

### Corrección post-archive del smoke test (28/03/2026)

Tras archivar el change, se detecto que el smoke test seguia apareciendo como
skipped incluso teniendo `REDDIT_API_KEY` en `.env`. La causa: `os.getenv()`
no lee ficheros `.env`; solo lee variables ya presentes en el entorno del
proceso. En ejecucion manual local, `.env` no se carga automaticamente salvo
que el shell lo haya hecho antes.

Dos cambios aplicados en un unico commit (`fix: load .env explicitly in Reddit
smoke test`):

1. `python-dotenv` anadido a dependencias dev en `pyproject.toml` y
   `uv.lock`. Es una dependencia transitiva de `pydantic-settings` que ya
   estaba presente en el entorno; formalizarla en dev deps la hace explicita.
2. `load_dotenv()` anadido antes del env-gate en `test_operational.py` para
   que `.env` se cargue en ejecucion local sin necesidad de pre-sourcear el
   entorno en el shell.
3. La variable de gate paso de `os.getenv("REDDIT_SMOKE_API_KEY")` a
   `os.getenv("REDDIT_SMOKE_API_KEY") or os.getenv("REDDIT_API_KEY")`.
   Prefiere una clave dedicada para smoke si existe, pero hace fallback a la
   clave general de Reddit que la mayoria de usuarios ya tienen en `.env`.

Resultado: 270 tests pasando, 0 skipped. El smoke test se ejecuta y pasa
contra la API real cuando `.env` esta configurado.

Los artefactos del change archivado (archive-report, verify-report, design,
tasks) se actualizaron para reflejar la correccion y los nuevos conteos.

Este caso es una leccion util para un junior: `os.getenv()` y la carga de
`.env` son dos cosas distintas. Los test runners no cargan `.env`
automaticamente salvo que se configure explicitamente (`python-dotenv`,
`pytest-dotenv`, o un `conftest.py` con `load_dotenv()`). Si un test parece
no ver variables que sabes que estan en `.env`, este es el primer lugar donde
mirar.
