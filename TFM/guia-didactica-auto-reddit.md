# Guia didactica de auto-reddit

Esta es una guia viva. Se construye junto al proyecto y crece con cada implementacion que se va completando.

Su objetivo no es solo explicar `auto-reddit`. Su objetivo es que un junior que empiece a leerla, aunque nunca haya visto el repo, entienda al terminar por que se toman decisiones de arquitectura, como se planifica trabajo con criterio de ingenieria, que son los contratos y por que importan, como funciona el desarrollo asistido por IA de verdad y, de paso, como esta construido concretamente este sistema.

No es un manual de onboarding. Es una guia de aprendizaje que usa un proyecto real como hilo conductor.

## Indice

- [Agradecimientos y herramientas usadas](#agradecimientos-y-herramientas-usadas)
- [0. Nota de honestidad](#0-nota-de-honestidad-sobre-esta-guia)
- [1. Proposito y como leerla](#1-proposito-de-la-guia-y-como-leerla)
- [2. Overview del proyecto](#2-overview-del-proyecto)
- [3. Que problema resuelve y que no hace](#3-problema-que-resuelve-y-limites)
- [4. Estado actual: scaffolding y madurez real](#4-estado-actual-scaffolding-y-madurez)
- [5. Project map](#5-project-map)
- [6. Glosario](#6-glosario)
- [7. Arquitectura explicada para juniors](#7-arquitectura-explicada-para-juniors)
- [8. Decisiones arquitectonicas con trade-offs](#8-decisiones-arquitectonicas-por-bloques-con-trade-offs)
- [9. OpenSpec, SDD, skills, AGENTS, GitNexus, Engram y MCP](#9-openspec-sdd-skills-agentsmd-gitnexus-y-engram-como-encajan)
- [10. Recorrido por carpetas y archivos Python](#10-recorrido-por-carpetas-y-archivos-python-relevantes)
- [11. Flujos del sistema](#11-flujos-principales-del-sistema)
- [12. Problemas, riesgos y mitigaciones](#12-problemas-riesgos-y-mitigaciones-conocidos)
- [13. Learning notes para juniors](#13-learning-notes-para-juniors)
- [14. Zonas pendientes o abiertas](#14-zonas-pendientes-o-incognitas)
- [15. Cierre](#15-cierre-que-es-hoy-auto-reddit-de-verdad)
- [16. Historial de changes](#16-historial-de-changes)
- [17. Como mantener viva esta guia](#17-como-mantener-viva-esta-guia)

La estructura separa cuatro capas que conviene no mezclar nunca: **producto**, **arquitectura**, **proceso y herramientas de trabajo**, e **implementacion real del momento**. Cada bloque tiene rotacion distinta: producto y arquitectura cambian poco; implementacion, riesgos y pendientes cambian con cada change. Cuando el proyecto crezca, añade en los bloques correspondientes; no abras una guia paralela.

## Agradecimientos y herramientas usadas

Este proyecto existe gracias a que hay gente que construye herramientas abiertas buenas y las documenta bien. Conviene nombrarlo, y conviene separarlo del producto, porque una cosa es `auto-reddit` y otra es el ecosistema con el que se piensa, documenta e implementa.

### El ecosistema de trabajo

Este proyecto no se construye con un editor y ganas. Se construye con un ecosistema pensado para trabajar con agentes de IA de forma disciplinada y reproducible. Conviene entenderlo porque, aunque ninguna de estas herramientas forma parte de `auto-reddit` como producto, todas condicionan como se piensa, como se documenta y como se implementa.

**OpenCode en modo agentico**
Es la interfaz desde la que el autor interactua con el repo y con los agentes. No es el agente en si; es el entorno que los orquesta. Piensalo como el IDE inteligente que coordina exploracion de codigo, edicion y memoria entre sesiones.

**gentle-ai — el ecosistema que lo sostiene todo**
`gentle-ai` ([github.com/Gentleman-Programming/gentle-ai](https://github.com/Gentleman-Programming/gentle-ai)) es un ecosistema de configuracion agentica creado por Gentleman Programming. Ofrece memoria persistente entre sesiones (Engram), soporte para skills, integracion con MCP y un workflow de desarrollo guiado por especificacion (SDD). Sustituye e integra lo que antes era Agent Teams Lite (ATL), que aparece referenciado en documentacion historica del proyecto como antecedente del mismo ecosistema.

En este proyecto, gentle-ai actua como infraestructura del proceso: es lo que permite que un agente recuerde lo que decidio en una sesion anterior, cargue instrucciones especificas para cada tipo de tarea y siga un workflow disciplinado en lugar de improvisar.

**Engram — memoria persistente**
Engram es la pieza de memoria de gentle-ai. Sin ella, cada sesion del agente empieza desde cero: sin contexto de decisiones pasadas, sin saber que se debuggo ayer ni por que se descarto cierta alternativa. Con Engram, el agente puede recuperar ese contexto y seguir donde lo dejo. En este proyecto se usa para guardar decisiones tecnicas, hallazgos de investigacion, bugfixes importantes y resumen de sesiones.

**GitNexus — inteligencia estructural del codigo**
GitNexus ([github.com/abhigyanpatwari/GitNexus](https://github.com/abhigyanpatwari/GitNexus)) construye un grafo de conocimiento del codigo: simbolos, relaciones entre ellos, flujos de ejecucion y comunidades funcionales. En `auto-reddit` esta verificado en `AGENTS.md` y `.gitnexus/meta.json`, donde el indice registra 592 simbolos, 644 relaciones y 3 execution flows.

Para que sirve en la practica: antes de modificar una funcion, puedes ver que otras partes del sistema dependen de ella. Antes de hacer un refactor, puedes saber el impacto real. Es la diferencia entre editar codigo a ciegas y editarlo con mapa.

**Skills globales y skills locales**
Una skill es un paquete de instrucciones especializadas para un agente. Le dice como debe abordar un tipo de tarea concreto: como explorar codigo, como implementar segun las convenciones del proyecto, como integrar con DeepSeek, como desplegar con Docker.

Las skills globales pertenecen al entorno del agente y son reutilizables en cualquier proyecto. Las skills locales viven en `skills/` dentro del repo y expresan las convenciones especificas de `auto-reddit`. Un agente que llega nuevo al proyecto carga las locales y sabe inmediatamente como debe trabajar aqui.

Esta separacion tiene valor arquitectonico: el repo no le exige al mundo que comparta el mismo entorno, pero tampoco deja sus propias reglas en la cabeza del autor.

**`product-discovery` y `skill-creator`**
`product-discovery` es una skill global que ayuda a definir bien un brief de producto antes de empezar a planificar implementacion. Sirve para hacer las preguntas correctas antes de comprometerse con una arquitectura. El autor la uso para trabajar la definicion inicial del sistema.

`skill-creator` es la skill que permite formalizar nuevas skills siguiendo una estructura y un contrato comunes. El autor declara que `product-discovery` fue creada con su ayuda; ese dato habla del nivel de madurez del ecosistema: las propias herramientas de trabajo se documentan con el mismo rigor que el producto.

### Los modelos que el autor usa como herramientas

El autor trabaja con varios modelos segun la fase: `GPT` para ciertos tipos de analisis y debate, `Claude Sonnet` y `Claude Opus` para implementacion y razonamiento tecnico complejo, `Gemini Pro` para otras tareas del flujo. La combinacion exacta varia por fase y tipo de tarea.

Es util entenderlo como flujo de trabajo declarado por el autor, no como dependencia tecnica de `auto-reddit`. El producto no necesita saber que modelo lo construyo para funcionar. Pero el desarrollador que quiera reproducir este proceso si tiene que saber que la calidad del resultado depende tanto de las herramientas de apoyo como del criterio de quien las dirige.

## 0. Nota de honestidad sobre esta guia

Esta guia se construye leyendo el codigo, la documentacion operativa, los artefactos OpenSpec, las notas del TFM ya existentes y la memoria contextual acumulada del proyecto en Engram. No pretende ser perfecta ni completa desde el primer dia: es un documento vivo que mejora con cada iteracion del proyecto.

Cuando algo en esta guia no ha podido verificarse directamente desde el repo o desde fuentes publicas, se indica de forma explicita. No encontraras afirmaciones presentadas como hechos cuando son hipotesis, ni tooling del autor confundido con funcionalidad del producto.

El indice GitNexus del repo, verificable en `.gitnexus/meta.json`, registra a fecha de esta revision 592 simbolos, 644 relaciones y 3 execution flows. Ese dato da una idea concreta del tamano estructural del proyecto en este momento.

---

## 1. Proposito de la guia y como leerla

### Que pretende este documento

Esta guia usa `auto-reddit` como excusa para ensenar. El proyecto es el hilo conductor, no el objetivo final.

Al terminar de leerla deberas ser capaz de:

- entender por que la arquitectura de software se diseña antes de codificar
- distinguir entre un contrato, una interfaz, un servicio y un adaptador, con ejemplos reales
- saber que es SDD, OpenSpec y por que importan mas de lo que parecen al principio
- entender como se trabaja con agentes de IA de forma disciplinada, no caotica
- leer un proyecto desconocido y saber que preguntas hacerte antes de tocar nada
- reconocer la diferencia entre madurez documental y madurez de implementacion
- entender que problema resuelve `auto-reddit`, como esta pensado y que le falta aun

No necesitas experiencia previa en el proyecto. Si necesitas curiosidad y ganas de entender el porqué de las cosas.

### Como leerla si eres junior

La mejor forma de leerla es esta:

1. Empieza por las secciones 2, 3 y 7 para entender el problema y la forma del sistema
2. Ve a la seccion 8 para ver como se toman decisiones de arquitectura con trade-offs reales
3. Estudia la seccion 9 para entender que son OpenSpec, SDD, skills, AGENTS, GitNexus y Engram, y como encajan
4. Recorre la seccion 10 para ver cada carpeta y archivo con su rol y su razon de existir
5. Termina con las secciones 12, 13 y 14: riesgos reales, lecciones directas y zonas abiertas

No hace falta leerla de una sentada. Cada seccion funciona de forma relativamente independiente.

### Idea fuerza

La frase que mejor resume el proyecto esta en `README.md`: la IA propone y el humano decide. Ese principio NO es marketing. Es un limite arquitectonico y de producto.

### Como esta organizada para crecer

La guia intenta no mezclar cuatro niveles que en proyectos con agentes se pisan enseguida:

1. producto (`docs/product/`)
2. arquitectura (`docs/architecture.md`, `docs/integrations/`)
3. proceso y herramientas de trabajo (`openspec/`, `AGENTS.md`, skills, GitNexus, Engram)
4. implementacion real del momento (`src/`, `tests/`, `scripts/`)

Si en futuras iteraciones aparece una nueva implementacion, un nuevo change SDD o una nueva herramienta, la regla es meter cada novedad en su nivel correspondiente y no contaminar los demas. Esa disciplina es la que permite que esta guia siga viva en lugar de convertirse en un diario caotico.

---

## 2. Overview del proyecto

`auto-reddit` es un sistema pensado para detectar cada dia oportunidades de participacion en Reddit alrededor de Odoo y entregarlas por Telegram a un equipo humano de marketing y contenido.

La vision operativa actual, verificable en `README.md`, `docs/product/product.md` y `docs/architecture.md`, es esta:

- fuente inicial: `r/Odoo`
- ventana temporal: ultimos 7 dias por fecha de creacion
- recorte downstream actual: hasta 8 candidatos revisados al dia laborable
- limite de envio: hasta 8 oportunidades al dia laborable
- entrega: Telegram
- publicacion final: manual, nunca automatica

### En una frase para juniors

No es un bot que publica. Es un sistema de vigilancia y preparacion de oportunidades.

### En una frase para arquitectos

Es un monolito modular Python orientado a pipeline diario efimero, con contratos Pydantic, estado minimo SQLite previsto, integracion multi-provider para Reddit y evaluacion IA diferida antes de entrega humana.

---

## 3. Problema que resuelve y limites

### El problema real

Seguir Reddit a mano para detectar conversaciones donde una empresa experta en Odoo podria aportar valor consume tiempo, depende mucho del criterio humano y cuesta repetirlo con disciplina cada dia.

El proyecto intenta reducir ese coste con un flujo como este:

1. detectar posts recientes relevantes
2. filtrar candidatos elegibles
3. enriquecer con contexto del hilo
4. pedir a la IA una evaluacion y una respuesta sugerida
5. entregar el resultado al equipo humano por Telegram

### Lo que SI hace el producto

- vigilar `r/Odoo`
- priorizar por recencia
- usar IA para ayudar a decidir si merece intervenir
- redactar borradores para revision humana
- evitar, a futuro, reenviar o reevaluar cosas ya decididas

### Lo que NO hace

- no publica autonomamente en Reddit
- no sustituye criterio editorial humano
- no es un sistema general de social listening multi-red ni multi-subreddit
- no tiene historico largo como feature principal
- no tiene backlog editorial formal en la version vigente

### Limites funcionales actuales

Segun `docs/product/product.md` y `docs/integrations/reddit/api-strategy.md`:

- el caso `old but alive` queda fuera de alcance
- el sistema se limita a dias laborables
- los comentarios no forman parte de la coleccion inicial; se recuperan despues, solo para posts ya seleccionados aguas arriba
- el flujo gratuito esta tensionado por cuotas, por eso el cap actual baja a 8/8

---

## 4. Estado actual, scaffolding y madurez

Esta es probablemente la parte mas importante para no enganarte.

### Estado real del repo — actualizado 2026-03-28 (pipeline completo)

Los cinco changes estan **completados y archivados**. El pipeline es funcional de extremo a extremo: recoge candidatos de Reddit, filtra por memoria, enriquece con contexto de hilo, evalua con IA y entrega al equipo humano por Telegram.

La base ejecutable incluye:

- trece contratos Pydantic en `shared/contracts.py` cubriendo todo el pipeline
- cliente Reddit con fallback chain para posts y comentarios
- `CandidateStore` SQLite con modelo de estados y purga de TTL
- evaluador IA con system prompt de dos fases, retry y validacion Pydantic estricta
- modulo `delivery/` con selector determinista, renderer HTML y cliente Telegram
- `main.py` con los cinco pasos del pipeline activos
- 259 tests: 50 + 20 + 37 + 56 + 96
- cinco specs canonicas en `openspec/specs/`

### Que esta maduro

- producto definido en `docs/product/product.md`
- reglas editoriales de IA en `docs/product/ai-style.md` con modelo recomendado
- arquitectura modular documentada y validada en cinco changes completos
- los cinco changes archivados con specs canonicas y trazabilidad completa
- skilling del repo y normas operativas consolidadas

### Que sigue scaffolded

Nada. El pipeline principal esta completo.

Lo que queda como trabajo potencial futuro: tests de integracion end-to-end entre modulos, observabilidad operativa avanzada, expansion a otros subreddits o fuentes.

### Nivel de madurez por capas

| Capa | Madurez | Comentario docente |
|---|---|---|
| Producto | Alta | Que, para que y limites bien cerrados. |
| Arquitectura | Alta | Validada en cinco changes completos de extremo a extremo. |
| Contratos / shared | Alta | Trece contratos implementados cubriendo todo el pipeline. |
| Integracion Reddit | Alta | Posts y comentarios con fallback chain y 87 tests. |
| Persistencia | Alta | `CandidateStore` con modelo de estados, TTL y 20 tests. |
| IA / evaluacion | Alta | Evaluador completo con prompt de dos fases, retry y 56 tests. |
| Delivery Telegram | Alta | Selector, renderer, cliente y 96 tests. |
| Testing | Alta | 259 tests cubriendo los cinco modulos del pipeline. |

### Lectura correcta de la madurez

El sistema es funcionalmente completo. Con las variables de entorno configuradas, ejecuta el pipeline diario entero: detecta, filtra, enriquece, evalua y entrega. Lo que no tiene aun es observabilidad avanzada, tests de integracion orquestados y cobertura de edge cases operativos que solo aparecen en produccion real.

---

## 5. Project map

### Mapa corto

```text
auto-reddit/
|- src/auto_reddit/
|   |- shared/contracts.py             13 contratos Pydantic — todo el pipeline
|   |- reddit/client.py                Fallback chain posts — change 1
|   |- reddit/comments.py             Fallback chain comentarios + ContextQuality — change 3
|   |- persistence/store.py            CandidateStore SQLite + purge_expired — changes 2 y 5
|   |- evaluation/evaluator.py         Evaluador IA DeepSeek con prompt 2 fases — change 4
|   |- evaluation/__init__.py          Expone evaluate_batch
|   |- delivery/selector.py            Seleccion determinista con TTL y retry-first — change 5
|   |- delivery/renderer.py            Renderizado HTML para Telegram — change 5
|   |- delivery/telegram.py            Cliente Bot API Telegram — change 5
|   |- delivery/__init__.py            Orquesta deliver_daily — change 5
|   |- main.py                         Pipeline completo: 5 pasos activos
|   |- config/settings.py              Configuracion y validacion de entorno
|- tests/
|   |- test_reddit/                    87 tests (changes 1 y 3)
|   |- test_persistence/               20 tests — change 2
|   |- test_evaluation/                56 tests — change 4
|   |- test_delivery/                  96 tests — change 5
|- docs/                               Fuente de verdad funcional y tecnica
|- openspec/
|   |- specs/                          Specs canonicas (fuente de verdad permanente)
|   |   |- reddit-candidate-collection/spec.md
|   |   |- candidate-memory/spec.md
|   |   |- thread-context-extraction/spec.md
|   |   |- ai-opportunity-evaluation/spec.md
|   |   |- telegram-daily-delivery/spec.md
|   |- changes/archive/                Todos los changes archivados
|   |   |- 2026-03-27-reddit-candidate-collection/
|   |   |- 2026-03-27-candidate-memory-and-uniqueness/
|   |   |- 2026-03-28-thread-context-extraction/
|   |   |- 2026-03-28-ai-opportunity-evaluation/
|   |   |- 2026-03-28-telegram-daily-delivery/
|- skills/                             Skills locales del repo
|- scripts/                            Tooling de investigacion, no flujo de producto
|- TFM/                                Documentacion academica
|- AGENTS.md / CLAUDE.md               Reglas operativas para agentes
```

### Mapa semantico

No pienses el repo por carpetas. Piensalo por capas:

1. `docs/` dice que producto y arquitectura queremos
2. `openspec/` dice como descomponemos e implementamos ese camino
3. `skills/` y `AGENTS.md` dicen como deben trabajar los agentes en este repo
4. `scripts/` ayuda a reducir incertidumbre tecnica antes de codificar
5. `src/auto_reddit/` sera la realizacion del sistema cuando los changes se implementen

### Mapa de verdad documental

| Pregunta | Documento fuente |
|---|---|
| Que problema resuelve el producto | `docs/product/product.md` |
| Como debe comportarse la IA | `docs/product/ai-style.md` |
| Como se organiza el sistema | `docs/architecture.md` |
| Que APIs de Reddit usar y con que fallback | `docs/integrations/reddit/api-strategy.md` |
| Como se esta planificando el trabajo | `openspec/` |
| Como deben trabajar los agentes | `AGENTS.md`, `CLAUDE.md`, `skills/` |

---

## 6. Glosario

### Conceptos de negocio

- `oportunidad`: post donde tiene sentido que el equipo humano considere intervenir
- `candidato`: post normalizado que aun no ha sido evaluado como oportunidad
- `hilo resuelto o cerrado`: conversacion donde intervenir ya no aporta valor real
- `recencia`: prioridad por fecha de creacion del post, no por ultima actividad

### Conceptos tecnicos

- `monolito modular`: una sola aplicacion con modulos bien separados, sin microservicios
- `contrato`: estructura de datos compartida entre modulos; en este repo es `RedditCandidate` en `shared/contracts.py`
- `DTO/modelo de transferencia`: objeto orientado a mover datos entre capas
- `fallback chain`: cadena ordenada de proveedores; si el primero falla se intenta el siguiente (`reddit3 → reddit34 → reddapi`)
- `normalizer`: funcion que transforma la respuesta heterogenea de una API externa al contrato propio del sistema
- `cursor`: token opaco que una API devuelve para indicar el punto de inicio de la pagina siguiente; cada provider de Reddit usa un campo distinto
- `is_complete`: campo computado de `RedditCandidate` que indica si el candidato tiene todos los campos minimos del contrato; los incompletos se conservan pero se marcan
- `idempotencia`: propiedad de una operacion que produce el mismo resultado si se ejecuta varias veces; en este sistema se logra con persistencia de estados (`sent`, `rejected`)
- `TTL`: tiempo de vida de un registro; aqui se piensa como `created_at + 7 dias`
- `scaffolding`: estructura inicial preparada pero aun sin implementacion real
- `blast radius`: conjunto de simbolos y modulos que se ven afectados cuando cambias uno concreto; se mide con `gitnexus_impact`
- `decision final`: estado que no puede revertirse en el modelo de negocio; aqui `sent` y `rejected` son finales; el post no vuelve a entrar al pipeline
- `estado transitorio`: estado operativo temporal que puede evolucionar; `pending_delivery` es transitorio porque representa "la IA dijo si, Telegram aun no confirma"
- `upsert`: operacion de base de datos que inserta si no existe o actualiza si ya existe; evita duplicados sin necesidad de consultar antes de escribir
- `idempotencia de reintentos`: capacidad de reintentar una operacion sin efectos secundarios adicionales; en este sistema, reintentar Telegram no re-evalua la IA porque `pending_delivery` guarda el resultado anterior
- `ContextQuality`: enum que indica la riqueza del contexto de hilo extraido segun el proveedor; `full` (reddit34 con arbol y timestamps), `partial` (reddit3 sin metadatos de anidamiento), `degraded` (reddapi solo top comments y plano)
- `ThreadContext`: contrato que empaqueta candidato original, lista de comentarios normalizados, calidad y proveedor; es la salida del change 3 y la entrada del change 4
- `depth / parent_id`: metadatos de anidamiento en un hilo de comentarios; reddit34 los expone, reddit3 no los incluye en sus campos (su arbol se recorre via `replies[]` pero no hay valor directo), reddapi no los tiene
- `structured output`: respuesta de un modelo de lenguaje forzada a cumplir un esquema JSON; en este proyecto DeepSeek devuelve un JSON validado por `AIRawResponse` — si no pasa Pydantic, el post se salta sin abortar el batch
- `dos fases en el prompt`: patron de diseno de prompts donde el modelo primero DECIDE (acepta/rechaza) y luego GENERA contenido; evita que la IA escriba una respuesta plausible y luego racionalice la aceptacion
- `prompt cacheado`: system prompt estatico que los modelos modernos pueden mantener en cache de prefijo para reducir latencia y coste; en este proyecto `_build_system_prompt()` devuelve siempre el mismo string
- `retry con tenacity`: libreria de Python para reintentos declarativos con decoradores; `@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))` es mas limpio y testeable que un bucle manual
- `union discriminada (EvaluationResult)`: tipo que puede ser `AcceptedOpportunity` o `RejectedPost`; el caller usa `isinstance()` para saber cual recibio, sin castings inseguros
- `retry-first selection`: politica de priorizacion en el selector de entregas; los registros que ya tuvieron un intento fallido de entrega se seleccionan antes que los nuevos dentro del cap diario; maximiza la probabilidad de que una oportunidad evaluada llegue al equipo
- `sent solo tras confirmacion`: el estado `sent` no se escribe en SQLite hasta que Telegram confirma la entrega; un fallo de red no produce un post marcado como enviado sin haberlo entregado
- `resumen no bloqueante`: el mensaje de resumen diario (fecha, posts revisados, oportunidades detectadas) se envia al final; si falla, las entregas individuales ya estan hechas y no se deshacen
- `TTL de entrega`: tiempo maximo de vida de un registro `pending_delivery`; en este sistema son 7 dias desde `decided_at`; pasado ese tiempo el post ya no es editorialmente relevante y se purga

### Conceptos de proceso

- `OpenSpec`: sistema de artefactos de planificacion en ficheros
- `SDD`: Spec-Driven Development, desarrollo guiado por especificacion
- `change`: slice vertical de trabajo dentro de OpenSpec
- `skill`: paquete de instrucciones especializadas para un agente
- `Engram`: memoria persistente entre sesiones
- `GitNexus`: capa de inteligencia estructural del codigo basada en grafo

---

## 7. Arquitectura explicada para juniors

### La idea base

Imagina una cocina profesional.

- un puesto recoge ingredientes
- otro decide si merecen entrar en el menu
- otro prepara el emplatado
- otro registra que ya se ha servido
- y un jefe de cocina coordina todo

Eso es exactamente lo que intenta hacer `auto-reddit`.

### Por que no meter todo en un solo archivo

Porque mezclar extraccion Reddit, evaluacion IA, persistencia y entrega Telegram en el mismo modulo crea acoplamiento y vuelve muy caro cambiar cualquier parte.

En este repo se decide lo contrario: separar responsabilidades desde el principio.

### Los bloques de la arquitectura

#### `reddit/`

Es la puerta de entrada de datos externos. Su trabajo no es decidir si un post merece respuesta. Su trabajo es traer posts y comentarios y normalizarlos.

#### `evaluation/`

Es la capa de juicio asistido por IA. Recibe candidatos ya limpios y devuelve una decision estructurada.

#### `delivery/`

Es la capa de salida. Convierte resultados evaluados en mensajes Telegram.

#### `persistence/`

Es la memoria operativa minima. Sirve para recordar que ya se envio o que ya se descarto un post.

#### `shared/`

Es el sitio donde viven los contratos comunes. Esto evita que cada modulo invente su propia forma de representar un post o una evaluacion.

#### `config/`

Carga settings y secretos. Su objetivo es fallar rapido si falta algo critico.

#### `main.py`

Es el director de orquesta. No deberia contener la logica de negocio fina. Solo deberia coordinar pasos.

### Regla de oro del repo

La arquitectura documentada insiste en esto: ningun modulo importa a otro modulo directamente. Todos hablan a traves de `shared/` y `config/`, y `main.py` los conecta.

### Por que esta regla es buena

Porque si `evaluation/` dependiera internamente de detalles de `reddit/`, cada cambio en Reddit romperia la evaluacion. Con contratos, cada modulo depende del idioma comun, no de la implementacion del vecino.

### Modelo operativo: contenedor efimero

El sistema no se piensa como un servidor vivo 24/7. Se piensa como un trabajo diario:

1. arranca
2. ejecuta el pipeline
3. envia resultados
4. termina

Eso simplifica mucho:

- menos complejidad de infraestructura
- menos estado vivo
- menos problemas de procesos colgados
- despliegue mas simple con cron externo

### La parte delicada: las APIs de Reddit

No hay una unica API perfecta. Por eso la arquitectura ya nace con idea de fallback.

Segun `docs/integrations/reddit/api-strategy.md`:

- posts: `reddit3 -> reddit34 -> reddapi`
- comentarios: `reddit34 -> reddit3 -> reddapi`

Esto ensena una leccion muy util: la arquitectura no se hace por gusto, sino porque la realidad externa obliga.

---

## 8. Decisiones arquitectonicas por bloques, con trade-offs

### 8.1 Monolito modular en vez de microservicios

**Decision:** un solo proyecto Python con modulos internos.

**Por que:** el problema aun es pequeno y esta cambiando mucho. Separarlo en servicios ahora seria sobrearquitectura.

**Trade-off:**

- ventaja: menos complejidad de despliegue y de coordinacion
- coste: si el sistema crece mucho, hara falta vigilar el acoplamiento interno

### 8.2 Contratos Pydantic explicitos

**Decision:** los datos entre modulos deben pasar por modelos compartidos.

**Por que:** las APIs Reddit son heterogeneas y la IA exige esquemas claros.

**Trade-off:**

- ventaja: validacion temprana y menos ambiguedad
- coste: obliga a disenar mejor antes de picar codigo

### 8.3 Contenedor efimero + cron externo

**Decision:** no tener daemon persistente.

**Por que:** el caso de uso es batch diario.

**Trade-off:**

- ventaja: operaciones simples, menos coste cognitivo
- coste: menos flexibilidad para eventos en tiempo real

### 8.4 Persistencia minima en SQLite

**Decision:** guardar solo lo necesario para idempotencia y unicidad.

**Por que:** el objetivo no es montar una plataforma editorial completa.

**Trade-off:**

- ventaja: simplicidad brutal
- coste: menos historico y menos analitica desde el principio

### 8.5 Sin backlog explicito en la version vigente

**Decision:** `approved` desaparece del modelo vigente y quedan `sent` y `rejected` como estados documentados.

**Por que:** se quiere evitar convertir un MVP de deteccion en una cola editorial compleja.

**Trade-off:**

- ventaja: reglas mas simples
- coste: menos control fino sobre items no tratados hoy

**Nota docente importante:** el repo conserva restos historicos donde si aparecia `approved` o incluso un modelo 10/10. Eso ya no es la referencia vigente.

### 8.6 Comentarios solo cuando el post ya ha pasado aguas arriba

**Decision:** no pedir comentarios en la coleccion inicial.

**Por que:** los comentarios son donde de verdad se quema cuota.

**Trade-off:**

- ventaja: ahorro de requests
- coste: la primera fase decide con menos contexto

### 8.7 Estrategia multi-provider para Reddit

**Decision:** repartir responsabilidades por proveedor y usar fallback.

**Por que:** ninguna API no oficial cubre bien todo con la cuota gratuita y calidad necesarias.

**Trade-off:**

- ventaja: resiliencia y mejor encaje por caso de uso
- coste: mas complejidad de normalizacion, pruebas y observabilidad

### 8.8 `User-Agent: RapidAPI Playground` para ReddAPI

**Decision documentada:** el script de snapshots fuerza ese `User-Agent` en `scripts/reddit_api_raw_snapshot.py` para ReddAPI.

**Por que:** la evidencia raw muestra el cambio 403 -> 200 cuando el cliente replica una firma aceptada por Cloudflare.

**Trade-off:**

- ventaja: recupera un fallback util
- coste: dependes de un detalle operativo externo y algo fragil

### 8.9 OpenSpec antes de implementar serio

**Decision:** descomponer en changes verticales antes de construir el producto completo.

**Por que:** evita mezclar demasiadas decisiones a la vez.

**Trade-off:**

- ventaja: mejor trazabilidad y menos caos
- coste: da sensacion de avance mas lento al principio

---

## 9. OpenSpec, SDD, skills, AGENTS.md, GitNexus, Engram y MCP: como encajan

Esta es la parte que convierte el repo en algo mas que codigo fuente.

### 9.1 OpenSpec

`openspec/` es la capa de artefactos de planificacion.

Segun `openspec/README.md`, el proyecto mantiene una secuencia de changes:

1. `reddit-candidate-collection`
2. `candidate-memory-and-uniqueness`
3. `thread-context-extraction`
4. `ai-opportunity-evaluation`
5. `telegram-daily-delivery`

OpenSpec sirve para evitar el error clasico de los juniors: ponerse a programar una idea grande sin haberla troceado.

### 9.2 SDD

SDD significa Spec-Driven Development. Aqui la idea no es "primero codifico y luego ya veremos". Aqui la idea es:

1. discovery del problema
2. proposal del change
3. spec funcional
4. design tecnico
5. tasks
6. apply
7. verify
8. archive

En este repo se ve muy bien en el change `reddit-candidate-collection`, que ya tiene discovery, proposal, spec, design y tasks.

### 9.3 Skills globales relevantes en este ecosistema

Ademas de las skills locales del repo, el entorno de trabajo de esta tarea expone una familia de skills globales. Eso es verificable en el runtime del agente, aunque no en un fichero `.atl/skill-registry.md` local.

Las familias mas relevantes para entender este proyecto son estas:

- **GitNexus**: `gitnexus-exploring`, `gitnexus-debugging`, `gitnexus-impact-analysis`, `gitnexus-refactoring`, `gitnexus-guide`, `gitnexus-cli` y `gitnexus-pr-review`. Su papel es navegar el codigo como grafo, no escribir el producto por si solos.
- **SDD**: `sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify` y `sdd-archive`. Juntas modelan el ciclo de trabajo por changes: descubrir, proponer, especificar, disenar, implementar, verificar y cerrar.
- **Descubrimiento y soporte al proceso**: `product-discovery` ayuda a definir bien un cambio antes de formalizarlo; `create-repo-context` sirve para crear o mantener ficheros de contexto como `AGENTS.md`; `skill-creator` sirve para empaquetar patrones recurrentes en nuevas skills reutilizables.

La leccion docente importante es esta: una skill global suele capturar metodo reusable. No habla de `auto-reddit` en concreto, sino de como pensar o ejecutar mejor un tipo de trabajo.

### 9.4 Skills locales del repo y por que importan

Las skills locales SI forman parte de la identidad operativa de `auto-reddit`, porque viven en `skills/` y estan referenciadas explicitamente desde `AGENTS.md`.

- `skills/python-conventions/SKILL.md`: fija la arquitectura modular, el uso de Pydantic para contratos, `uv` como interfaz de trabajo y el reparto de responsabilidades entre modulos.
- `skills/deepseek-integration/SKILL.md`: aterriza como conectar con DeepSeek a traves del SDK de OpenAI, como exigir structured output y como manejar errores sin esconder excepciones.
- `skills/docker-deployment/SKILL.md`: consolida el modelo de contenedor efimero, volumen para SQLite y cron externo en VPS.

Por eso importan tanto: convierten decisiones dispersas del repo en instrucciones accionables. No son propaganda de tooling; son una forma de evitar que un agente nuevo improvise donde el proyecto ya habia decidido.

### 9.5 `AGENTS.md`

`AGENTS.md` es la capa de reglas de operacion para agentes dentro de este repo.

Aqui fija:

- entorno (`uv`, Python 3.14, `.env.example`)
- restricciones (no publicar autonomamente en Reddit)
- estructura del paquete (`src/auto_reddit/`)
- skills del proyecto
- reglas GitNexus para explorar, refactorizar y verificar cambios

En otras palabras: `AGENTS.md` hace explicito el "manual de taller" del repo.

### 9.6 GitNexus

GitNexus es la capa de inteligencia estructural del codigo. Aunque en esta tarea no he ejecutado consultas interactivas al grafo, el repo deja claro su papel:

- explorar arquitectura y execution flows
- medir blast radius antes de tocar simbolos
- detectar alcance real de cambios antes de commit
- hacer renombres con mas seguridad

La metadata verificable en `.gitnexus/meta.json` dice que el indice tiene:

- 87 files
- 592 nodes
- 644 edges
- 5 communities
- 3 processes

La leccion docente aqui es potente: no solo tienes codigo, tambien tienes una representacion navegable del codigo.

### 9.7 Engram

Engram es la memoria persistente entre sesiones de agentes.

En este proyecto resulta util para:

- recordar decisiones ya tomadas
- guardar hallazgos tecnicos, como el fix del `User-Agent` de ReddAPI
- no perder contexto del planning y los cambios documentales

En otras palabras, OpenSpec guarda artefactos formales del trabajo y Engram guarda memoria operativa del trabajo.

### 9.8 Como se trabaja concretamente en este proyecto

El autor usa un flujo agentico por fases. Cada fase tiene un tipo de trabajo distinto y usa la herramienta mas adecuada para ese trabajo:

- **Discovery y definicion de producto**: se trabaja con `product-discovery` para formular el problema antes de planificar nada
- **Propuesta, spec, design y tasks**: se producen artefactos SDD con agentes especializados, uno por fase, para no mezclar el que con el como
- **Implementacion**: el agente recibe el contexto de spec y design y produce codigo siguiendo las skills locales del repo
- **Verificacion**: un agente revisa que la implementacion cumple la spec antes de dar el change por cerrado
- **Tests**: se automatizan como parte del proceso de verificacion, no como afterthought
- **Debate de alternativas y analisis de problemas**: se usan los modelos como interlocutores tecnicos para contrastar opciones y razonar trade-offs antes de decidir

Este flujo demuestra algo importante para un junior: la IA no es un sustituto del criterio de ingenieria. Es una herramienta que amplifica ese criterio cuando el que la usa sabe exactamente que le esta pidiendo y por que.

### 9.9 MCP: el protocolo que conecta agentes con herramientas

MCP son las siglas de Model Context Protocol. Es el protocolo estandar que permite a un agente de IA usar herramientas externas reales: leer memoria, consultar un grafo de codigo, buscar en bases de datos, ejecutar comandos, acceder a APIs.

Sin MCP, el agente solo tiene texto. Con MCP, el agente puede actuar.

La analogia mas util: si el agente es un cirujano, MCP es el instrumental quirurgico. Sin instrumentos, el conocimiento no alcanza. Con ellos, puede operar con precision.

#### Como funciona MCP en la practica

Un servidor MCP expone un conjunto de herramientas y/o recursos. El agente puede llamar esas herramientas durante una sesion, igual que llama a funciones. La diferencia con una funcion normal es que el servidor MCP corre fuera del modelo: es un proceso externo que el agente invoca, no logica interna suya.

Esto tiene una consecuencia importante: **el agente no sabe por si solo que herramientas tiene disponibles**. Las herramientas se configuran en el entorno donde corre el agente, no en el modelo. Por eso en este repo no encontraras un `.mcp.json` dentro de la carpeta del proyecto: la configuracion MCP vive en el entorno del autor, no en el producto `auto-reddit`.

#### Los servidores MCP activos en este proyecto

En este repo hay dos servidores MCP que el agente usa activamente durante el desarrollo.

**GitNexus MCP**

Este es el MCP mas visible en el repo. Su presencia esta verificada explicitamente en `AGENTS.md`, donde se documentan las herramientas que los agentes deben usar antes de editar codigo.

Las herramientas que expone, con ejemplos reales del repo:

| Herramienta | Para que sirve | Ejemplo concreto en auto-reddit |
|---|---|---|
| `gitnexus_query` | Encontrar codigo por concepto | `gitnexus_query({query: "reddit fallback"})` para localizar donde se gestiona el fallback entre providers |
| `gitnexus_context` | Ver callers, callees y flujos de un simbolo | `gitnexus_context({name: "collect_candidates"})` para ver quien llama a esa funcion y a quien llama |
| `gitnexus_impact` | Calcular blast radius antes de editar | `gitnexus_impact({target: "RedditCandidate", direction: "upstream"})` para saber que se romperia si cambias el contrato |
| `gitnexus_detect_changes` | Verificar alcance real antes de commit | `gitnexus_detect_changes({scope: "staged"})` para confirmar que solo tus cambios previstos han tocado el grafo |
| `gitnexus_rename` | Renombrar simbolos de forma segura | `gitnexus_rename({symbol_name: "RedditCandidate", new_name: "RedditPost", dry_run: true})` para previsualizar el impacto |
| `gitnexus_cypher` | Consultas custom al grafo de conocimiento | `gitnexus_cypher({query: "MATCH (n)-[:CALLS]->(m) WHERE n.name='main' RETURN m"})` para ver todos los simbolos que llama main |

Ademas de herramientas, GitNexus expone recursos legibles directamente:

```
gitnexus://repo/auto-reddit/context       — vision general del repo e indice actual
gitnexus://repo/auto-reddit/clusters      — areas funcionales del codigo
gitnexus://repo/auto-reddit/processes     — todos los flujos de ejecucion identificados
gitnexus://repo/auto-reddit/process/{name} — traza paso a paso de un flujo concreto
```

La leccion para un junior es esta: antes de editar cualquier funcion en este repo, se espera que el agente haya corrido `gitnexus_impact` sobre ella. Ese protocolo esta escrito en `AGENTS.md` como regla, no como sugerencia.

**Engram MCP**

Engram tambien es un servidor MCP. Lo que el agente llama `mem_save`, `mem_search`, `mem_context` o `mem_get_observation` son herramientas de ese servidor.

Ejemplos reales de lo que Engram ha guardado en este proyecto durante el desarrollo:

- el bugfix de ReddAPI: cuando se descubrio que el script fallaba por un `User-Agent` incorrecto, se guardo en Engram con tipo `bugfix`, titulo y contexto. La proxima sesion, el agente puede recuperarlo sin que el autor tenga que repetir todo el contexto.
- las decisiones del cap de 8/dia: cuando se decidio bajar el limite de 10 a 8, Engram guardo la razon. Las sesiones posteriores que tocaron documentacion relacionada recuperaron ese contexto antes de editar.
- el resumen de cada sesion: al cerrar una sesion larga de trabajo, el agente guarda un resumen estructurado con objetivo, descubrimientos, lo que se completo y los proximos pasos. Sin esto, cada sesion empezaria desde cero.

La diferencia entre Engram y un archivo de notas manual es que el agente puede buscar en Engram con lenguaje natural y recuperar observaciones concretas. No es busqueda por nombre de archivo; es busqueda semantica sobre lo que se guardo.

#### Lo que MCP permite que no seria posible sin el

Sin MCP, el agente trabaja con texto: lee lo que le das y responde. Con MCP:

- puede consultar el grafo de codigo antes de editar
- puede recuperar memoria de sesiones anteriores
- puede verificar el impacto real de un cambio antes de cometerlo
- puede buscar en la historia de decisiones del proyecto sin que el autor tenga que recordarlas

Eso es lo que convierte un modelo de lenguaje en un agente capaz de trabajar de forma sostenida en un proyecto real.

---

### 9.10 Como encaja todo junto

La mejor forma de verlo es esta:

| Capa | Funcion |
|---|---|
| `docs/` | Define verdad funcional y tecnica |
| `openspec/` | Descompone el camino de entrega |
| `skills/` | Estandariza como debe trabajar el agente dentro de este repo |
| `AGENTS.md` | Orquesta reglas, restricciones y uso de MCPs del repo |
| Skills globales | Aportan metodo reusable entre proyectos |
| GitNexus MCP | Da inteligencia estructural del codigo en tiempo de trabajo |
| Engram MCP | Conserva memoria operativa entre sesiones |
| `src/` | Implementa el producto |

Eso, dicho claro, es ingenieria de producto. No solo programacion.

---

## 10. Recorrido por carpetas y archivos Python relevantes

En esta seccion no solo digo que contiene cada archivo. Explico por que existe y que papel juega en la arquitectura.

### 10.1 Raiz del proyecto

#### `README.md`

Es el mejor punto de entrada general. Resume descripcion, stack, estructura, funcionalidades y reglas operativas del MVP.

Rol: documento de onboarding rapido.

#### `pyproject.toml`

Verifica decisiones importantes:

- nombre del paquete
- `requires-python = ">=3.14"`
- dependencias runtime: `pydantic`, `pydantic-settings`, `openai`
- dependencias dev: `pytest`, `pytest-cov`
- src-layout con Hatchling

Rol: contrato de build y dependencias.

#### `Dockerfile`

Materializa el modelo efimero:

- usa `python:3.14-slim`
- copia `uv`
- instala la app en sistema con `uv pip install --system --no-cache .`
- arranca con `python -m auto_reddit.main`

Rol: empaquetado de ejecucion.

**Lectura honesta:** hoy ese entrypoint apunta a un `main.py` vacio de logica, asi que el contenedor esta alineado con la arquitectura prevista, pero no con una funcionalidad completa.

#### `docker-compose.yml`

Define un servicio `auto-reddit` con:

- build local
- `env_file: .env`
- volumen `sqlite_data:/data`
- `restart: "no"`

Rol: orquestacion local/minima del contenedor y preparacion de persistencia por volumen.

### 10.2 `src/auto_reddit/`

#### `src/auto_reddit/main.py`

**Changes 1 y 2 implementados.**

La funcion `run()` ya orquesta los dos primeros pasos del pipeline y deja marcados con comentarios los siguientes:

```python
def run() -> None:
    # Change 2: inicializar store
    store = CandidateStore(settings.db_path)
    store.init_db()

    # Change 1: recoger candidatos (ventana 7 dias, sin recorte)
    candidates = collect_candidates(settings)

    # Change 2: excluir decisiones finales y recortar a 8
    decided_ids = store.get_decided_post_ids()
    eligible = [c for c in candidates if c.post_id not in decided_ids]
    review_set = eligible[:settings.daily_review_limit]

    # Change 3 (pendiente): enriquecer con comentarios
    # Change 4 (pendiente): evaluacion IA → store.save_pending_delivery / save_rejected
    # Change 5 (pendiente): entrega Telegram → store.mark_sent
```

Rol: director de orquesta. Cada change nuevo conecta aqui sin tocar los anteriores.

Con el change 5 integrado, `main.py` tiene el pipeline completo:

```python
store = CandidateStore(settings.db_path); store.init_db()          # change 2
candidates = collect_candidates(settings)                           # change 1
review_set = eligible[:settings.daily_review_limit]                 # change 2
thread_contexts = fetch_thread_contexts(review_set, settings)       # change 3
evaluation_results = evaluate_batch(thread_contexts, settings)      # change 4
for result in evaluation_results:
    if isinstance(result, AcceptedOpportunity):
        store.save_pending_delivery(result.post_id, result.model_dump_json())
    else:
        store.save_rejected(result.post_id)
report = deliver_daily(store, settings,                             # change 5
                       reviewed_post_count=len(review_set))
```

**Leccion docente:** este archivo es el mejor resumen del sistema. Cinco lineas logicas, cinco responsabilidades separadas, cinco modulos que no se conocen entre si. Cada change añadio exactamente una linea al orquestador sin tocar las anteriores. Eso es lo que hace que la arquitectura modular valga la pena.

#### `src/auto_reddit/evaluation/evaluator.py`

**Change 4 implementado.** El modulo mas complejo del proyecto hasta ahora.

Su estructura interna:

**`_SYSTEM_PROMPT_TEMPLATE`** — el system prompt estatico. Cacheable por los modelos modernos. Define el rol del evaluador (forero habitual de Reddit, sesgo por defecto hacia NO intervenir), el proceso obligatorio de dos fases (DECIDE primero, GENERA despues), la regla de abstension con sus cinco condiciones de aceptacion, las categorias excluidas, los tipos de oportunidad y rechazo cerrados, las reglas editoriales y la politica de idioma. Es largo y explicito porque la ambiguedad en el prompt se convierte en comportamiento impredecible del modelo.

**`_build_user_message(ctx)`** — construye el mensaje de usuario deterministico. Incluye subreddit, titulo, URL, calidad del contexto, contenido del post, comentarios y, si la calidad es degradada, un aviso explicito al modelo.

**`_evaluate_single_raw(ctx, client, model)`** — llamada a DeepSeek sin retry. Crea la request, parsea el JSON, valida con `AIRawResponse`, y construye `AcceptedOpportunity` o `RejectedPost`. Los campos `post_id`, `title` y `link` vienen del pipeline, no de la IA.

**`evaluate_batch(thread_contexts, settings)`** — punto de entrada publico. Itera el dict `post_id → ThreadContext`, llama al evaluador con retry de tenacity (backoff exponencial), salta posts que fallan todos los reintentos sin abortar el batch.

Rol: capa de juicio asistido. Transforma contexto bruto en decisiones justificadas con estructura definida.

#### `src/auto_reddit/config/settings.py`

Es uno de los pocos ficheros con implementacion real. Define `Settings` usando `BaseSettings`.

Campos verificados:

- `deepseek_api_key`
- `telegram_bot_token`
- `telegram_chat_id`
- `reddit_api_key`
- `max_daily_opportunities = 10`
- `review_window_days = 7`
- `daily_review_limit = 10`

Rol: configuracion y validacion de entorno.

**Detalle docente importante:** el archivo instancIa `settings = Settings()` a nivel de modulo. Eso significa que la validacion ocurre al importar, no solo al ejecutar el flujo principal.

**Tension verificada:** los defaults siguen en `10`, pero la documentacion vigente y el design del change 1 ya hablan de `8`. Este gap esta incluso recogido como tarea OpenSpec (`openspec/changes/reddit-candidate-collection/tasks.md`).

#### `src/auto_reddit/shared/contracts.py`

**Changes 1 y 2 implementados.** Este archivo es el idioma comun de todo el sistema.

Contiene tres contratos:

**`RedditCandidate`** (change 1) — el candidato normalizado que sale del cliente Reddit:

```python
class RedditCandidate(BaseModel):
    post_id: str
    title: str
    selftext: str | None = None
    url: str            # siempre URL absoluta
    permalink: str      # siempre URL absoluta
    author: str | None = None
    subreddit: str
    created_utc: int
    num_comments: int | None = None
    source_api: str

    @computed_field
    @property
    def is_complete(self) -> bool: ...  # True si todos los campos minimos presentes
```

**`PostDecision`** (change 2) — enum de estados de decision:

```python
class PostDecision(str, Enum):
    sent = "sent"                         # entregado a Telegram — decision final
    rejected = "rejected"                 # rechazado por IA — decision final
    pending_delivery = "pending_delivery" # IA acepto, Telegram aun no confirma
```

`pending_delivery` es el estado mas interesante didacticamente: representa la frontera entre la decision de negocio (la IA evaluo) y la confirmacion operativa (Telegram entrego). Sin ese estado, un fallo de Telegram obligaria a re-evaluar con IA, lo que consume cuota y puede cambiar el resultado.

**`PostRecord`** (change 2) — el registro persistido en SQLite:

```python
class PostRecord(BaseModel):
    post_id: str
    status: PostDecision
    opportunity_data: str | None = None  # JSON del resultado IA para reintentos
    decided_at: int                      # Unix timestamp
```

`opportunity_data` permite reintentar la entrega Telegram usando el resultado ya guardado de la IA, sin volver a llamarla.

Leccion docente sobre contratos: **un buen contrato no solo describe datos; describe semantica**. `pending_delivery` no es un estado tecnico de implementacion; es una decision de diseno que protege la idempotencia del sistema y el presupuesto de API.

**`ContextQuality`** (change 3) — enum que indica la riqueza del contexto extraido:

```python
class ContextQuality(str, Enum):
    full     = "full"      # reddit34: arbol, timestamps, sort=new garantizado
    partial  = "partial"   # reddit3: lista recursiva, sin depth/parent_id
    degraded = "degraded"  # reddapi: solo top comments, plano, sin timestamps
```

**`RedditComment`** (change 3) — comentario normalizado con campos opcionales segun proveedor:

```python
class RedditComment(BaseModel):
    comment_id: str | None = None   # None en reddapi
    author: str | None = None
    body: str                       # normalizado desde text/content/body/comment
    score: int | None = None
    created_utc: int | None = None  # None en reddapi; ISO 8601 en reddit34
    permalink: str | None = None
    parent_id: str | None = None    # None en reddit3 y reddapi
    depth: int | None = None        # None en reddit3 y reddapi
    source_api: str
```

**`ThreadContext`** (change 3) — salida del paso de extraccion, entrada del paso de evaluacion IA:

```python
class ThreadContext(BaseModel):
    candidate: RedditCandidate
    comments: list[RedditComment]
    comment_count: int
    quality: ContextQuality
    source_api: str
```

Esta separacion entre extraccion y evaluacion es una decision de diseno importante: el modulo de comentarios no sabe si el post merece respuesta; solo extrae y normaliza. La decision es del modulo de evaluacion.

**Contratos del change 4** (evaluacion IA):

```python
class OpportunityType(str, Enum):
    funcionalidad = "funcionalidad"        # preguntas sobre configuracion de Odoo
    desarrollo = "desarrollo"              # desarrollo, modulos, codigo Python
    dudas_si_merece_la_pena = "..."        # dudas sobre si Odoo vale para un caso
    comparativas = "comparativas"          # comparativas con otras herramientas

class RejectionType(str, Enum):
    resolved_or_closed = "..."             # hilo cerrado o resuelto
    no_useful_contribution = "..."         # nada util que anadir
    excluded_topic = "..."                 # tema excluido o de riesgo
    insufficient_evidence = "..."          # contexto insuficiente para evaluar

class AIRawResponse(BaseModel):
    accept: bool
    opportunity_type: OpportunityType | None = None
    opportunity_reason: str | None = None  # por que aporta valor (no es el resumen)
    post_summary_es: str | None = None
    comment_summary_es: str | None = None  # None si no hay comentarios utiles
    suggested_response_es: str | None = None
    suggested_response_en: str | None = None
    post_language: str | None = None       # unico campo detectado por la IA
    rejection_type: RejectionType | None = None
    warning: str | None = None             # solo en aceptaciones con calidad degradada
    human_review_bullets: list[str] | None = None  # idem

class AcceptedOpportunity(BaseModel):     # campos deterministicos + generados por IA
    post_id: str; title: str; link: str   # nunca pedidos a la IA
    opportunity_type: OpportunityType
    opportunity_reason: str
    post_summary_es: str
    comment_summary_es: str | None = None
    suggested_response_es: str
    suggested_response_en: str
    warning: str | None = None
    human_review_bullets: list[str] | None = None

class RejectedPost(BaseModel):
    post_id: str
    rejection_type: RejectionType         # sin warning ni bullets — no aplican

EvaluationResult = Annotated[Union[AcceptedOpportunity, RejectedPost], ...]
```

**Leccion clave:** los campos `post_id`, `title` y `link` los construye el pipeline, no la IA. La IA solo genera lo que requiere razonamiento. Esta separacion evita alucinaciones en campos deterministicos y hace la validacion Pydantic mucho mas fiable.

**Otra leccion:** `warning` y `human_review_bullets` solo existen en `AcceptedOpportunity`. Si un post es rechazado, el humano no necesita esas senales — solo necesita saber el tipo de rechazo. Este nivel de granularidad en el contrato comunica la intencion del diseno sin necesidad de comentarios.

**`DeliveryReport`** (change 5) — informe de una ejecucion de entrega:

```python
class DeliveryReport(BaseModel):
    total_selected: int    # candidatos seleccionados por el selector (≤ cap)
    retries: int           # reintentos (ya tuvieron intento previo fallido)
    new: int               # nuevos (primer intento)
    sent_ok: int           # mensajes individuales entregados con exito
    sent_failed: int       # mensajes que fallaron en Telegram
    summary_sent: bool     # True si el mensaje de resumen se envio con exito
    expired_skipped: int   # registros excluidos por TTL expirado
```

`DeliveryReport` no es solo un log; es el contrato que permite al orquestador loguear con precision lo que paso en cada ciclo de entrega y detectar anomalias (muchos `sent_failed`, `expired_skipped` alto, etc.).

Rol: idioma comun del sistema. Ningun modulo importa de otro directamente; todos hablan a traves de este archivo.

#### `src/auto_reddit/reddit/client.py`

**Change 1 implementado.** Este es el archivo mas rico del proyecto en este momento: 348 lineas de codigo real, bien estructurado, con separacion clara de responsabilidades internas.

Su estructura interna merece un recorrido docente:

**Normalizers por provider** (`_normalize_reddit3`, `_normalize_reddit34`, `_normalize_reddapi`)
Cada funcion sabe exactamente como transformar la forma especifica de una API al contrato `RedditCandidate`. Estan separadas porque cada API tiene una estructura distinta. Esta decision evita condicionales anidados en el codigo principal.

```python
# reddit3: posts planos en body[]
# reddit34: posts en data.posts[].data
# reddapi: posts en posts[].data
```

**Helper `_to_absolute_url`**
Pequeña funcion con un trabajo muy claro: si la URL es relativa, la convierte a absoluta. Extraida como helper para no repetirla tres veces. Es un ejemplo perfecto de DRY aplicado con criterio.

**Cursor extractors** (`_cursor_reddit3`, `_cursor_reddit34`, `_cursor_reddapi`)
La ubicacion del cursor de paginacion es distinta en cada API. En lugar de un condicional en el bucle de paginacion, cada provider tiene su extractor. El bucle no sabe nada de las diferencias; recibe una funcion y la llama.

```python
# reddit3:  response.meta.cursor
# reddit34: response.data.cursor
# reddapi:  response.cursor
```

Esta fue una incognita abierta durante el diseno que se resolvio verificando los raws reales.

**`_fetch_with_retry`**
Reintentos con backoff exponencial (2s, 4s). Cualquier excepcion se loggea y se reintenta hasta agotar los intentos. Si todo falla, lanza `RuntimeError`. La decision de no silenciar errores es correcta: el fallo de un provider debe ser visible, no invisible.

**`_paginate`**
Funcion generica de paginacion que no sabe nada del provider concreto. Recibe: URL, headers, params base, nombre del param de cursor, normalizer y extractor de cursor. Pagina hasta que no hay mas cursor o hasta que el post mas antiguo de la pagina esta fuera de la ventana de 7 dias.

**`collect_candidates`** — el punto de entrada publico
Implementa el fallback chain: `reddit3 → reddit34 → reddapi`. Si un provider lanza excepcion, pasa al siguiente. Si todos fallan, devuelve lista vacia y logea error. Aplica dos filtros sobre el resultado del provider ganador: ventana de 7 dias y subreddit == "odoo" (case-insensitive). Devuelve ordenado por recencia descendente.

Rol: adaptador de entrada del sistema. Absorbe la heterogeneidad de tres APIs externas y entrega un contrato homogeneo al siguiente paso del pipeline.

#### `src/auto_reddit/persistence/store.py` (ampliado en change 5)

El change 5 añadio `purge_expired(post_ids)` a `CandidateStore`:

```python
def purge_expired(self, post_ids: list[str]) -> int:
    """Elimina registros pending_delivery con TTL expirado."""
```

Llamado por `deliver_daily` al final del ciclo con la lista de `post_id` que el selector descarto por TTL. Limpia SQLite de registros que ya no pueden entregarse. Devuelve el numero de filas eliminadas.

El selector identifica los registros expirados antes de construir el set de entrega; `purge_expired` los borra despues de que el ciclo ha terminado.

#### `src/auto_reddit/delivery/` (change 5)

Modulo nuevo con cuatro colaboradores. La separacion de responsabilidades aqui es especialmente clara:

**`selector.py`** — `select_deliveries(records, now, cap)` → `(selected, expired_post_ids)`

Recibe todos los registros `pending_delivery`, filtra los expirados (TTL > 7 dias), ordena reintentos antes que nuevos, excluye registros con `opportunity_data` malformed antes de consumir el cap, y devuelve el set seleccionado mas la lista de expirados para purga. No sabe nada de Telegram.

**`renderer.py`** — `render_opportunity(opp)` y `render_summary(date, reviewed, opportunities)`

Renderiza mensajes Telegram en HTML. `render_opportunity` formatea un mensaje por oportunidad aceptada. `render_summary` genera el mensaje de resumen diario con fecha, posts revisados y numero de oportunidades — campos exigidos explicitamente en `product.md §10`. No sabe nada de SQLite.

**`telegram.py`** — `send_message(token, chat_id, text)` → `bool`

Cliente minimo de la Bot API de Telegram: una llamada HTTP POST, devuelve `True` si Telegram responde 200. Sin logica de negocio, sin estado. La responsabilidad de reintentar o saltar es del orquestador, no del cliente.

**`__init__.py`** — `deliver_daily(store, settings, reviewed_post_count)` → `DeliveryReport`

El orquestador de delivery. Conecta los tres colaboradores:
1. obtiene `pending_delivery` del store
2. llama al selector para el set del dia
3. para cada registro seleccionado: renderiza, envia, marca `sent` solo si Telegram confirma
4. envia el mensaje de resumen (no bloqueante: fallo no deshace entregas)
5. purga expirados del store
6. devuelve `DeliveryReport`

Leccion docente clave: este modulo demuestra que una responsabilidad compleja (entregar con retry, respetar el cap, no re-evaluar la IA, purgar TTL) se puede implementar de forma legible cuando se separa en colaboradores con contratos claros.

#### `src/auto_reddit/reddit/comments.py`

**Change 3 implementado.** Modulo nuevo, analogo a `client.py` pero para comentarios.

Punto de entrada publico: `fetch_thread_contexts(review_set, settings) → dict[str, ThreadContext]`.

Internamente tiene la misma arquitectura que `client.py`:

- un normalizer por proveedor (`_normalize_reddit34_comments`, `_normalize_reddit3_comments`, `_normalize_reddapi_comments`)
- fallback chain: `reddit34 → reddit3 → reddapi`
- si todos los providers fallan para un post, ese post queda fuera del dict resultado (no bloquea el pipeline)

**Diferencia clave frente al fallback de posts:** el fallback de comentarios esta ordenado de forma distinta. `reddit34` es el proveedor primario para comentarios porque ofrece `sort=new`, timestamps ISO 8601, `parent_id`, `depth` y arbol de replies. `reddit3` como fallback parcial: tiene el arbol recursivo via `replies[]` pero no expone `depth` ni `parent_id` como campos directos. `reddapi` como fallback degradado: solo top comments, plano, sin timestamps ni identificadores de comentario.

**Detalle tecnico de reddit34:** el campo `created` de comentarios llega como string ISO 8601 (`"2026-03-27T13:46:04.000000+0000"`), no como unix timestamp. El normalizer aplica `datetime.fromisoformat(v.replace("+0000", "+00:00"))` antes de convertir a int.

**Detalle tecnico de reddit3:** los comentarios se recorren recursivamente via `replies[]`. Se podria derivar un `depth` sintetico contando niveles de recursion, pero eso no es equivalente a un `depth` real que viene del API. Decision explicita: `depth=None` y `parent_id=None` para todos los comentarios de reddit3, reflejado en `ContextQuality.partial`.

Rol: adaptador de entrada de contexto de hilo. Normaliza la heterogeneidad de las APIs de comentarios al contrato `ThreadContext`.

#### `src/auto_reddit/evaluation/evaluator.py`

Contenido real verificado: una docstring.

Rol esperado:

- aplicar criterio IA
- devolver decision estructurada

Rol actual: placeholder de la capa de juicio.

#### `src/auto_reddit/delivery/telegram.py`

Contenido real verificado: una docstring.

Rol esperado:

- formatear mensajes
- enviarlos a Telegram

Rol actual: placeholder de la salida del sistema.

#### `src/auto_reddit/persistence/store.py`

**Change 2 implementado.** Ya no es un placeholder.

Contiene `CandidateStore`, la clase que gestiona la memoria operativa del sistema via SQLite:

```python
class CandidateStore:
    def init_db(self) -> None                                    # crea tabla si no existe
    def get_decided_post_ids(self) -> set[str]                   # sent + rejected (NO pending)
    def save_rejected(self, post_id: str) -> None                # upsert como rejected
    def save_pending_delivery(self, post_id: str, data: str)     # upsert como pending_delivery
    def mark_sent(self, post_id: str) -> None                    # transicion pending → sent
    def get_pending_deliveries(self) -> list[PostRecord]         # para reintentos Telegram
```

El detalle mas importante de diseno esta en `get_decided_post_ids`: devuelve `sent` y `rejected` pero **NO** `pending_delivery`. Esto es intencional: un post en `pending_delivery` debe seguir siendo elegible para reintento. Si lo incluyeras en los decididos, bloquearias el reintento y perderia la oportunidad.

Todos los metodos de escritura usan `INSERT ... ON CONFLICT DO UPDATE` (upsert), lo que hace las operaciones idempotentes: ejecutarlas dos veces produce el mismo resultado que ejecutarlas una.

La tabla SQLite tiene esta forma:

```sql
CREATE TABLE post_decisions (
    post_id          TEXT PRIMARY KEY,
    status           TEXT NOT NULL,       -- sent | rejected | pending_delivery
    opportunity_data TEXT,                -- JSON del resultado IA (nullable)
    decided_at       INTEGER NOT NULL     -- Unix timestamp
)
```

Rol: memoria operativa minima. No es una base de datos editorial completa; es exactamente lo necesario para garantizar unicidad de posts entre ejecuciones diarias y permitir reintentos sin re-evaluar la IA.

### 10.3 `scripts/`

#### `scripts/reddit_api_raw_snapshot.py`

Este es, junto a `settings.py`, el fichero de codigo mas importante que SI existe hoy de verdad.

Que hace:

- llama endpoints de `reddit3`, `reddit34`, `reddapi` y `reddit-com`
- guarda un JSON por llamada en `docs/integrations/reddit/<provider>/raw/`
- conserva request, headers, tiempos, respuesta y payload crudo

Por que existe:

Porque antes de programar adaptadores de producto hay que validar shapes y comportamientos reales. Este script es investigacion reproducible, no producto.

Detalles tecnicos docentes muy buenos:

- usa `dataclass` para `SnapshotContext` y `EndpointSpec`
- separa especificacion del endpoint, construccion de URL, headers, fetch y guardado
- redacciona headers sensibles antes de persistir raws
- incorpora el fix de ReddAPI con `REDDAPI_USER_AGENT = "RapidAPI Playground"`

Rol arquitectonico: reduce incertidumbre antes de disenar e implementar `reddit/client.py`.

### 10.4 `docs/`

#### `docs/product/product.md`

Es la fuente de verdad funcional del slice actual.

Rol: producto.

#### `docs/product/ai-style.md`

Define comportamiento esperado de la IA, tono, limites editoriales y politica de idioma.

Rol: politica de evaluacion y redaccion, no implementacion.

#### `docs/architecture.md`

Define la arquitectura fundacional.

Rol: decisiones tecnicas de alto nivel.

#### `docs/integrations/reddit/api-strategy.md`

Es probablemente el documento tecnico operativo mas importante ahora mismo.

Rol: fuente vigente de estrategia externa.

#### `docs/integrations/reddit/comparison.md`

Compara proveedores y justifica descartes o fallback.

Rol: soporte comparativo e historico.

#### `docs/integrations/reddit/*/README.md`

Cada uno documenta una API concreta con ejemplos, limites y veredicto.

Rol: base tecnica detallada por proveedor.

### 10.5 `openspec/`

#### `openspec/config.yaml`

Traduce al plano SDD las reglas del proyecto: stack, comandos, verdad de producto, verify, etc.

Rol: contrato operativo del proceso SDD.

#### `openspec/discovery/reddit-candidate-collection.md`

Captura el problema, flujo principal, alcance y readiness del change 1.

Rol: discovery estructurado.

#### `openspec/changes/reddit-candidate-collection/proposal.md`

Delimita intent, scope, risks, rollback y success criteria.

Rol: propuesta ejecutable del slice.

#### `openspec/changes/reddit-candidate-collection/specs/reddit-candidate-collection/spec.md`

Formula requirements y scenarios estilo Given/When/Then.

Rol: especificacion funcional verificable.

#### `openspec/changes/reddit-candidate-collection/design.md`

Baja la spec a decisiones tecnicas concretas: normalizadores, cursor pagination, fallback whole-step, etc.

Rol: diseno tecnico.

#### `openspec/changes/reddit-candidate-collection/tasks.md`

Convierte el design en trabajo implementable.

Rol: plan de ejecucion.

### 10.6 `skills/`

#### `skills/python-conventions/SKILL.md`

Es una especie de guia de estilo + arquitectura del proyecto para codigo Python.

Rol: convencion de implementacion.

#### `skills/deepseek-integration/SKILL.md`

Define como conectar con DeepSeek via SDK de OpenAI y structured output.

Rol: convencion de integracion IA.

#### `skills/docker-deployment/SKILL.md`

No se ha recorrido en detalle en esta tarea, pero su existencia esta verificada por `AGENTS.md` y el arbol del repo.

Rol: convencion de despliegue.

### 10.7 `tests/`

**Los cinco changes implementados.**

`tests/test_reddit/` — 87 tests (changes 1 y 3)

`tests/test_persistence/` — 20 tests (change 2)

`tests/test_evaluation/` — 56 tests (change 4)

`tests/test_delivery/` — 96 tests (change 5):
- `test_selector.py`: seleccion con cap, retry-first, exclusion de malformed, TTL, mezcla de reintentos y nuevos
- `test_renderer.py`: formato HTML de oportunidades, campos del resumen exigidos por `product.md §10`, escape de caracteres especiales
- `test_telegram.py`: llamadas HTTP mockeadas, respuesta 200 y error
- `test_deliver_daily.py`: ciclo completo con mocks de store y Telegram; `sent` solo tras confirmacion; resumen no bloqueante; purga de expirados; `DeliveryReport` correcto

Total: **259 tests pasando**.

Advertencias preservadas del verify (no blockers): no existe test de dos ejecuciones consecutivas que pruebe "skipped today, eligible tomorrow"; no existe test end-to-end de reintento Telegram sin re-evaluar IA. Ambas son pruebas de integracion que requieren estado entre runs y no estan cubiertas aun.

Rol actual: cobertura funcional de los dos primeros modulos del pipeline. Evaluacion, enriquecimiento y delivery siguen sin cobertura.

Leccion importante: 70 tests reales sobre los modulos criticos da una base solida para seguir construyendo con confianza. Pero los tests de integracion entre runs son distintos de los tests unitarios y requieren un enfoque diferente.

### 10.8 `TFM/`

Antes de esta guia ya existian al menos:

- `TFM/motivacion.md`
- `TFM/diario.md`

Rol: trazabilidad academica.

`TFM/diario.md` es especialmente util porque deja ver la evolucion del pensamiento del proyecto, incluidas decisiones historicas que luego fueron refinadas.

---

## 11. Flujos principales del sistema

Como el codigo del producto aun no esta implementado, aqui conviene distinguir entre flujo previsto y flujo actualmente ejecutable.

### 11.1 Flujo funcional previsto del producto

1. `main.py` comprueba si es dia laborable
2. `reddit/client.py` recoge todos los posts de `r/Odoo` de los ultimos 7 dias
3. `persistence/store.py` excluye posts ya marcados `sent` o `rejected`
4. se recortan los 8 elegibles mas recientes
5. `reddit/client.py` recupera comentarios solo para esos posts seleccionados
6. `evaluation/evaluator.py` decide si hay oportunidad y genera resumen + respuestas sugeridas
7. `delivery/telegram.py` envia resumen diario y mensajes por oportunidad
8. `persistence/store.py` registra estado para unicidad e idempotencia

### 11.2 Flujo del change 1 — IMPLEMENTADO Y ARCHIVADO

El change `reddit-candidate-collection` ya no es un flujo previsto: es codigo ejecutable verificado con 50 tests.

```
collect_candidates(settings)
  ├── Intenta reddit3
  │     ├── _paginate() con cursor reddit3
  │     │     └── _fetch_with_retry() → _normalize_reddit3() → [RedditCandidate]
  │     └── Si excepcion → siguiente provider
  ├── Intenta reddit34 (si reddit3 fallo)
  │     ├── _paginate() con cursor reddit34
  │     │     └── _fetch_with_retry() → _normalize_reddit34() → [RedditCandidate]
  │     └── Si excepcion → siguiente provider
  ├── Intenta reddapi (si reddit34 fallo)
  │     └── _paginate() con cursor reddapi + User-Agent obligatorio
  │           └── _fetch_with_retry() → _normalize_reddapi() → [RedditCandidate]
  └── Sobre el resultado del provider ganador:
        ├── Filtro: created_utc >= now - 7 dias
        ├── Filtro: subreddit.lower() == "odoo"
        └── Sort: created_utc descendente → [RedditCandidate] ordenados
```

Cada candidato lleva `is_complete=True/False` calculado automaticamente al construirse. Los incompletos no se descartan: quedan en la lista para que el paso siguiente decida.

### 11.3 Flujo de investigacion tecnica real ya existente

Este SI existe y SI funciona hoy, porque esta soportado por `scripts/reddit_api_raw_snapshot.py`:

1. leer API key
2. construir contexto de snapshot
3. recorrer endpoints definidos en `endpoint_specs()`
4. llamar a cada endpoint
5. guardar JSON raw por llamada
6. dejar evidencia en `docs/integrations/reddit/*/raw/`

### 11.4 Flujo operativo de documentacion y planning

Tambien hay un flujo muy real, aunque no sea el producto final:

1. discovery de idea y limites
2. consolidacion de producto y arquitectura
3. investigacion tecnica de APIs
4. revalidacion con raws
5. descomposicion OpenSpec
6. design del change
7. tasks previas a implementacion

Esto es valioso en un TFM porque enseña que la ingenieria seria empieza mucho antes del `def main():`.

### 11.5 Flujo completo ejecutable hoy

Con `DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` y `REDDIT_API_KEY` configuradas, el sistema ejecuta el pipeline completo:

1. Inicializa `CandidateStore` y la tabla SQLite
2. Recolecta candidatos de r/Odoo via fallback chain de posts
3. Excluye decididos, recorta a 8, extrae contexto de comentarios via fallback chain de comentarios
4. Evalua con DeepSeek: decision justificada por post, persiste aceptados como `pending_delivery` y rechazados como `rejected`
5. Selecciona registros `pending_delivery` con retry-first y cap 8, excluye malformed y expirados
6. Renderiza mensajes HTML, envia cada oportunidad a Telegram, marca `sent` solo tras confirmacion
7. Envia mensaje de resumen diario (no bloqueante)
8. Purga registros expirados de SQLite
9. Logea el `DeliveryReport` con todos los contadores del ciclo

El sistema es operativo. No es un prototipo ni un scaffolding: es un pipeline diario funcional.

---

## 12. Problemas, riesgos y mitigaciones conocidos

### 12.1 Cuotas gratuitas tensionadas

**Riesgo:** el modelo historico 10/10 no aguanta bien con la capacidad realmente util.

**Evidencia:** `docs/integrations/reddit/api-strategy.md` y `comparison.md` consolidan un modelo operativo 8/8 con margen aproximado de `~22 req/mes` antes de paginacion extra.

**Mitigacion:** bajar cap a 8 y recuperar comentarios solo aguas abajo.

### 12.2 Ninguna API de Reddit sirve sola para todo

**Riesgo:** si dependes de un unico proveedor, te quedas corto o en posts o en comentarios o en semantica real.

**Mitigacion:** estrategia multi-provider y fallback.

### 12.3 ReddAPI es util pero fragil

**Riesgo:** su operatividad depende de reproducir un `User-Agent` aceptado.

**Mitigacion:** dejar el detalle capturado y documentado; no tratar ReddAPI como principal para comentarios.

### 12.4 Gap entre documentacion vigente y codigo real

**Riesgo:** un desarrollador puede leer solo `src/` y pensar que falta todo, o leer solo `TFM/diario.md` y llevarse decisiones historicas superadas.

**Mitigacion:** respetar la jerarquia de verdad documental: `docs/product/product.md` + `docs/integrations/reddit/api-strategy.md` + `docs/architecture.md`.

### 12.5 Defaults desalineados

**Riesgo:** `settings.py` sigue en 10/10 cuando la referencia vigente es 8/8.

**Mitigacion:** el propio OpenSpec ya lo convierte en tarea explicita.

### 12.6 Estado de persistencia todavia ambiguo en algun resto del repo

**Riesgo:** `store.py` habla de 3 estados, y `TFM/diario.md` conserva fases antiguas con `approved`.

**Mitigacion:** tomar como vigente el modelo documentado actual de `sent` y `rejected`, sin backlog explicito.

### 12.7 Sin tests reales todavia

**Riesgo:** cuando empiece la implementacion, la regresion sera facil si no se aterrizan tests pronto.

**Mitigacion:** el design y tasks del change 1 ya contemplan fixtures raw y unit tests por normalizador, filtro temporal, paginacion y fallback.

### 12.8 Riesgo de sobreconfiar en la IA

**Riesgo:** convertir la IA en actor autonomo o propagandistico.

**Mitigacion:** `docs/product/ai-style.md` y la regla base del producto limitan claramente su papel.

---

## 13. Learning notes para juniors

### 13.1 Primero entiende el problema, luego el codigo

Aqui se ve clarisimo. El repo tiene mejor definido el problema que la implementacion. Y eso es bueno. Muchisimo mejor eso que tener 2000 lineas de codigo sobre una idea confusa.

### 13.2 La arquitectura no sale del aire

El reparto `reddit/`, `evaluation/`, `delivery/`, `persistence/`, `shared/`, `config/` no es decorativo. Sale de responsabilidades reales diferentes.

### 13.3 Un documento puede ser mas importante que una funcion

`docs/integrations/reddit/api-strategy.md` condiciona mas el exito del proyecto hoy que cualquier funcion de `src/auto_reddit/`, porque decide como sobrevivir a proveedores imperfectos.

### 13.4 No confundas scaffold con producto terminado

Ver carpetas y archivos no significa que el sistema ya exista. Hay que mirar dentro.

### 13.5 Las decisiones cambian; la trazabilidad importa

En `TFM/diario.md` veras decisiones antiguas como 10/10, `approved` o ciertas priorizaciones previas. Eso no es "malo". Es evidencia de aprendizaje y refinamiento. Lo importante es saber que documento manda hoy.

### 13.6 La investigacion tecnica tambien es ingenieria

`scripts/reddit_api_raw_snapshot.py` demuestra una practica buenisima: antes de prometer una integracion, captura evidencia reproducible.

### 13.7 Diseñar contratos pronto ahorra dolor despues

El design del change 1 ya propone `RedditCandidate` con campos concretos e `is_complete`. Ese tipo de decision evita peleas posteriores entre modulos.

### 13.8 Menos automatizacion puede ser mejor producto

No autopublicar en Reddit no es una carencia. Es una decision de riesgo, reputacion y control humano.

### 13.9 Herramientas de proceso tambien son arquitectura

OpenSpec, skills, AGENTS, GitNexus y Engram no son accesorios. Son parte del sistema socio-tecnico que hace sostenible el proyecto.

### 13.10 Aprende a distinguir cuatro niveles

Cuando leas un repo como este, distingue siempre:

1. verdad de producto
2. verdad arquitectonica
3. verdad de planning
4. verdad de implementacion actual

Muchisimos errores vienen de mezclar esas cuatro capas.

---

## 14. Zonas pendientes o incognitas

### 14.1 Implementacion funcional del pipeline — PARCIALMENTE RESUELTA

El change 1 esta completado y archivado. El pipeline de recoleccion de candidatos funciona.

Pendiente: changes 2 al 5 (filtrado por memoria, comentarios, evaluacion IA y entrega Telegram).

### 14.2 Parametros exactos de paginacion — RESUELTA

La incognita sobre la ubicacion del cursor en cada provider quedo cerrada al verificar los raws reales:

- `reddit3`: `response.meta.cursor`
- `reddit34`: `response.data.cursor`
- `reddapi`: `response.cursor`

El codigo implementado en `client.py` usa esta informacion verificada.

### 14.3 Modelo final de persistencia materializado — RESUELTA

`CandidateStore` implementado en `persistence/store.py` con estados `sent`, `rejected` y `pending_delivery`. Archivado en change 2.

### 14.4 Contratos reales de evaluacion IA

Hay ejemplos conceptuales en `shared/contracts.py` y en la skill de DeepSeek, pero no un contrato productivo cerrado ya implementado.

### 14.5 Formato final de mensajes Telegram en codigo

El documento de producto lo define, pero el modulo de delivery aun no lo materializa.

### 14.6 Observabilidad real del sistema en ejecucion

La arquitectura habla de stdout con contadores y errores, pero todavia no hay logging real en el pipeline del producto.

### 14.7 Contradicciones historicas que conviene limpiar en el futuro

- defaults 10/10 en `src/auto_reddit/config/settings.py` (la operativa vigente es 8, aunque `daily_review_limit` ya es correcto en la logica de `main.py`)
- entradas antiguas de `TFM/diario.md` con `approved`, 10/10 o formulaciones ya superadas

La docstring de `store.py` ya no es una contradiccion: la implementacion real usa el modelo de 3 estados correcto.

### 14.8 Tests de integracion entre ejecuciones — ABIERTA

El verify del change 2 dejo dos advertencias no bloqueantes:
- no existe test que pruebe "skipped today, eligible tomorrow" en dos runs consecutivos
- no existe test end-to-end de reintento Telegram usando `pending_delivery` sin re-llamar a la IA

Estas pruebas requieren estado persistente entre runs y un enfoque de integracion distinto al unitario. Quedan pendientes para cuando el pipeline este mas completo.

---

## 15. Cierre: que es hoy auto-reddit de verdad

Cinco changes completados. Doscientos cincuenta y nueve tests pasando. El pipeline es funcional de extremo a extremo.

Lo que existe hoy:

- recoleccion de candidatos con fallback chain entre tres providers de posts
- memoria operativa SQLite con unicidad, modelo de estados y TTL
- extraccion de contexto de hilo con calidad graduada segun proveedor de comentarios
- evaluacion IA con DeepSeek: prompt de dos fases, decision justificada, respuesta sugerida en dos idiomas, tipos cerrados de oportunidad y rechazo
- entrega determinista a Telegram: retry-first, cap, HTML formateado, `sent` solo tras confirmacion, resumen diario, purga de expirados
- `main.py` como mapa completo del pipeline en cinco lineas logicas

Si ejecutas el sistema hoy con las cuatro variables de entorno configuradas, detecta oportunidades en r/Odoo, evalua cuales merecen respuesta y las entrega al equipo humano por Telegram con resumen del dia.

Si tuviera que resumirlo para un junior:

> Cinco modulos, cinco responsabilidades, trece contratos, doscientos cincuenta y nueve tests, cinco changes archivados con trazabilidad completa. Se construyo de afuera hacia adentro: primero el problema, luego la arquitectura, luego cada capa en orden. El resultado es un sistema que cualquiera puede leer, entender y extender.

El proyecto no termina aqui. Termina la primera version del pipeline principal. Lo que sigue — observabilidad, tests de integracion, expansion a otras fuentes — tiene una base solida sobre la que construir.

---

## 16. Historial de changes

Esta seccion se actualiza cada vez que un change completa el ciclo SDD completo (apply + verify + archive). Es el registro vivo del avance real del proyecto.

### Change 1 — `reddit-candidate-collection` — ARCHIVADO 2026-03-27

**Alcance:** recoger todos los posts de `r/Odoo` de los ultimos 7 dias y entregarlos normalizados al siguiente paso del pipeline.

**Lo que implemento:**

- `shared/contracts.py`: `RedditCandidate` con `is_complete` como computed field
- `reddit/client.py`: tres normalizers, tres cursor extractors, `_fetch_with_retry`, `_paginate` generico y `collect_candidates` con fallback chain
- `main.py`: funcion `run()` con comentarios explicitando los changes pendientes
- `tests/test_reddit/`: 50 tests con fixtures de raws reales

**Decisiones tecnicas clave:**

- los candidatos incompletos se conservan con `is_complete=False`; no se descartan
- `url` y `permalink` se canonican a URL absoluta en el normalizer, no en el consumidor
- el subreddit se filtra post-normalizacion con `subreddit.lower() == "odoo"` como guard explicito
- el fallback chain es whole-step: si un provider falla en cualquier punto, se descarta entero y se intenta el siguiente; no hay fallback parcial por pagina
- `User-Agent: RapidAPI Playground` es obligatorio para reddapi; sin el, Cloudflare devuelve 403

**Spec canonica:** `openspec/specs/reddit-candidate-collection/spec.md`

**Archivo:** `openspec/changes/archive/2026-03-27-reddit-candidate-collection/`

**Verificacion:** PASS — 21/21 tasks completas, 50 tests pasando, 6 escenarios de spec cubiertos

### Change 5 — `telegram-daily-delivery` — ARCHIVADO 2026-03-28

**Alcance:** entrega determinista de oportunidades aceptadas al equipo humano por Telegram, con retry-first dentro del cap diario, `sent` solo tras confirmacion, resumen no bloqueante y purga de registros expirados por TTL.

**Lo que implemento:**

- `shared/contracts.py`: `DeliveryReport` con contadores del ciclo de entrega
- `persistence/store.py`: `purge_expired(post_ids)` para limpiar registros TTL expirados
- `delivery/selector.py`: `select_deliveries` — retry-first, exclusion de malformed, TTL 7 dias, devuelve seleccionados y expirados
- `delivery/renderer.py`: `render_opportunity` y `render_summary` — mensajes HTML con campos exigidos por `product.md §10`
- `delivery/telegram.py`: `send_message` — cliente minimo Bot API
- `delivery/__init__.py`: `deliver_daily` — orquestador del ciclo completo
- `main.py`: change 5 activo, pipeline completo
- `tests/test_delivery/`: 96 tests en cuatro ficheros

**Decisiones tecnicas clave:**

- retry-first: reintentos antes que nuevos dentro del cap; maximiza entrega de oportunidades ya evaluadas
- `sent` solo tras confirmacion de Telegram; nunca antes
- resumen no bloqueante: su fallo no deshace entregas individuales
- exclusion de malformed antes de consumir el cap (correccion post-verify)
- TTL de 7 dias: pasada esa ventana el post ya no es editorialmente relevante
- `reviewed_post_count` pasado desde upstream para el resumen de Telegram

**Spec canonica:** `openspec/specs/telegram-daily-delivery/spec.md`

**Archivo:** `openspec/changes/archive/2026-03-28-telegram-daily-delivery/`

**Verificacion:** PASS CON ADVERTENCIAS — 18/18 tasks completas, 259 tests pasando; advertencia de baja severidad sobre ausencia de test de orquestacion end-to-end que pruebe que delivery nunca re-entra en evaluacion IA

**Estado del proyecto:** pipeline principal completo — cinco changes archivados

---

### Change 4 — `ai-opportunity-evaluation` — ARCHIVADO 2026-03-28

**Alcance:** evaluar con IA los posts enriquecidos con contexto de hilo, producir decisiones justificadas (aceptado/rechazado) con estructura definida para revision humana y persistir el resultado para entrega Telegram sin re-evaluar.

**Lo que implemento:**

- `shared/contracts.py`: seis nuevos contratos — `OpportunityType`, `RejectionType`, `AIRawResponse`, `AcceptedOpportunity`, `RejectedPost`, `EvaluationResult`
- `evaluation/evaluator.py`: system prompt de dos fases, constructor de mensaje deterministico, llamada a DeepSeek con retry tenacity, validacion Pydantic, `evaluate_batch`
- `evaluation/__init__.py`: expone `evaluate_batch`
- `main.py`: change 4 activo — persiste aceptados como `pending_delivery` y rechazados como `rejected`
- `tests/test_evaluation/`: 56 tests en `test_contracts.py` y `test_evaluator.py`

**Decisiones tecnicas clave:**

- prompt de dos fases (DECIDE → GENERA) para evitar racionalizacion post-hoc
- campos deterministicos (`post_id`, `title`, `link`) construidos por el pipeline, nunca pedidos a la IA
- `warning`/`human_review_bullets` solo en `AcceptedOpportunity` con calidad degradada; `RejectedPost` no los lleva
- `opportunity_data` en `pending_delivery` guarda el JSON de `AcceptedOpportunity` para que el change 5 pueda reintentar Telegram sin re-evaluar la IA
- sistema de tipos cerrado con enums validados por Pydantic; cualquier valor fuera del esquema falla antes de llegar al pipeline
- retry/skip por post: si un post falla todos los reintentos, se salta sin abortar el batch
- ciclo correctivo post-verify: se alinearon contratos e implementacion con la regla de que `warning`/`bullets` solo aplican a aceptaciones

**Spec canonica:** `openspec/specs/ai-opportunity-evaluation/spec.md`

**Archivo:** `openspec/changes/archive/2026-03-28-ai-opportunity-evaluation/`

**Verificacion:** PASS CON ADVERTENCIAS — 37/37 tasks completas, 163 tests pasando; advertencias de baja severidad sobre pruebas de integracion end-to-end pendientes

---

### Change 3 — `thread-context-extraction` — ARCHIVADO 2026-03-28

**Alcance:** enriquecer solo los posts ya seleccionados aguas arriba con el contexto bruto normalizado de su hilo de comentarios, sin mezclar extraccion con evaluacion IA ni con entrega.

**Lo que implemento:**

- `shared/contracts.py`: `ContextQuality` enum, `RedditComment` con campos opcionales segun proveedor y `ThreadContext` como salida del paso
- `reddit/comments.py`: modulo nuevo con `fetch_thread_contexts`, normalizers por proveedor y fallback chain `reddit34 → reddit3 → reddapi`
- `main.py`: change 3 conectado, placeholder de change 4 actualizado
- `tests/test_reddit/test_comments.py`: 37 tests nuevos

**Decisiones tecnicas clave:**

- el fallback de comentarios esta ordenado diferente al de posts: `reddit34` primero porque tiene `sort=new`, timestamps, `depth` y `parent_id`; `reddit3` como parcial sin metadatos de anidamiento; `reddapi` degradado sin timestamps ni ids de comentario
- reddit34 devuelve `created` como ISO 8601 string, no unix; el normalizer aplica `fromisoformat` con sustitucion de timezone antes de convertir
- reddit3 no tiene `depth`/`parent_id` en sus campos directos; derivarlos sinteticamente desde la posicion del arbol no es equivalente a un valor real; decision: `None` para ambos + `ContextQuality.partial`
- si todos los providers fallan para un post, ese post queda fuera del dict de resultados; el pipeline no se rompe

**Spec canonica:** `openspec/specs/thread-context-extraction/spec.md`

**Archivo:** `openspec/changes/archive/2026-03-28-thread-context-extraction/`

**Verificacion:** PASS — 14/14 tasks completas, 107 tests pasando, 7/7 escenarios de spec cubiertos; el primer verify detecto discrepancia de wording en artefactos sobre reddit3 y depth, resuelta alineando design y tasks sin cambiar codigo

---

### Change 2 — `candidate-memory-and-uniqueness` — ARCHIVADO 2026-03-27

**Alcance:** memoria operativa minima y unicidad por post para que el pipeline diario no reprocese decisiones finales y pueda reintentar Telegram sin volver a llamar a la IA.

**Lo que implemento:**

- `shared/contracts.py`: `PostDecision` enum (`sent`, `rejected`, `pending_delivery`) y `PostRecord`
- `persistence/store.py`: `CandidateStore` con SQLite — init, upserts, transiciones de estado, consulta de decididos y pendientes de entrega
- `main.py`: integracion del store en el pipeline — exclusion de decididos, recorte a 8, placeholders comentados para changes 3-5
- `config/settings.py`: campo `db_path` para la ruta del fichero SQLite
- `tests/test_persistence/test_store.py`: 20 tests unitarios

**Decisiones tecnicas clave:**

- `get_decided_post_ids()` devuelve `sent` + `rejected` pero NO `pending_delivery`; los posts en `pending_delivery` siguen elegibles para reintento sin re-evaluar la IA
- todos los writes usan upsert (`INSERT ... ON CONFLICT DO UPDATE`) — idempotentes por diseno
- `opportunity_data` en `PostRecord` guarda el JSON del resultado IA para reintentar Telegram sin re-llamar al modelo
- el estado transitorio se llama `pending_delivery`, no `approved`; el nombre comunica exactamente la semantica: la IA dijo si, Telegram no ha confirmado aun

**Spec canonica:** `openspec/specs/candidate-memory/spec.md`

**Archivo:** `openspec/changes/archive/2026-03-27-candidate-memory-and-uniqueness/`

**Verificacion:** PASS CON ADVERTENCIAS — 16/16 tasks completas, 70 tests pasando; advertencias no bloqueantes sobre ausencia de tests de integracion entre runs

---

## 17. Como mantener viva esta guia

Si esta guia quiere seguir siendo util cuando lleguen nuevas implementaciones, tiene que actualizarse con reglas claras y no a golpe de intuicion.

### 17.1 Jerarquia de verdad documental

Cuando haya contradicciones, actualiza la guia siguiendo este orden:

1. `docs/product/` para verdad funcional
2. `docs/architecture.md` y `docs/integrations/` para verdad tecnica
3. `openspec/` para el plan vigente por change
4. `src/` y `tests/` para implementacion real materializada
5. `TFM/diario.md` y notas historicas como contexto, nunca como fuente vigente por defecto

### 17.2 Regla editorial clave

Cada actualizacion debe distinguir SIEMPRE entre:

- **producto**: lo que `auto-reddit` hace o debe hacer
- **herramienta de trabajo**: lo que ayuda a pensar, documentar, analizar o programar
- **flujo declarado por el autor**: decisiones de proceso no demostrables solo con el repo

Si se mezclan esas tres capas, la guia pierde valor academico y tecnico.

### 17.3 Cuando actualizar cada bloque

- actualiza la seccion 4 cuando cambie el nivel de madurez real de un modulo
- actualiza la seccion 9 cuando entren o salgan tools, skills o reglas de agente que afecten al proceso
- actualiza la seccion 10 cuando un placeholder pase a tener implementacion real o aparezcan nuevos modulos
- actualiza la seccion 11 cuando un flujo previsto pase a ser un flujo ejecutable
- actualiza la seccion 12 cuando un riesgo cambie de estado o aparezca una mitigacion nueva
- actualiza la seccion 14 cuando una incognita quede resuelta o nazcan otras nuevas

### 17.4 Como anadir futuros changes SDD sin romper la guia

Cuando se implemente un nuevo change, no reescribas la guia completa. Haz esto:

1. anade el change al mapa de proceso de la seccion 9
2. refleja en la seccion 10 que archivos o modulos se materializaron
3. mueve en la seccion 11 lo que ya sea flujo ejecutable
4. revisa secciones 12 y 14 para cerrar riesgos y abrir nuevos pendientes
5. anade una entrada en la seccion 16 con los datos del change archivado

### 17.5 Que no hacer

- no copiar trozos enteros de `README.md`, `docs/` u `openspec/` si no aportan sintesis
- no presentar tooling del autor como si fuera parte obligatoria del runtime del producto
- no ocultar limites de verificacion: si algo no se pudo demostrar desde repo o fuente publica, debe etiquetarse
- no dejar convivir sin nota decisiones historicas y decisiones vigentes
