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
- [16. Como mantener viva esta guia](#16-como-mantener-viva-esta-guia)

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

### Estado real del repo

El proyecto tiene mucha definicion y poca implementacion funcional todavia.

Eso NO significa que este mal hecho. Significa que esta en una fase donde se ha trabajado muy en serio el problema, la arquitectura, la investigacion tecnica y el planning, pero el codigo de negocio sigue en estado inicial.

### Que esta maduro

- producto bastante bien definido en `docs/product/product.md`
- reglas editoriales de IA bastante bien definidas en `docs/product/ai-style.md`
- arquitectura modular claramente documentada en `docs/architecture.md`
- estrategia Reddit bastante trabajada y revalidada con raws reales en `docs/integrations/reddit/`
- artefactos OpenSpec del change 1 muy avanzados: discovery, proposal, spec, design y tasks
- skilling del repo y normas operativas para agentes bastante elaboradas

### Que sigue scaffolded

- `src/auto_reddit/main.py` solo contiene una docstring
- `src/auto_reddit/reddit/client.py` solo contiene una docstring
- `src/auto_reddit/evaluation/evaluator.py` solo contiene una docstring
- `src/auto_reddit/delivery/telegram.py` solo contiene una docstring
- `src/auto_reddit/persistence/store.py` solo contiene una docstring
- `src/auto_reddit/shared/contracts.py` solo contiene comentarios de ejemplo
- los tests reales todavia no existen; en `tests/` solo hay `__init__.py`

### Nivel de madurez por capas

| Capa | Madurez | Comentario docente |
|---|---|---|
| Producto | Alta | El que, para que y limites estan bastante bien cerrados. |
| Arquitectura | Media-alta | La forma del sistema esta definida, aunque aun no se haya materializado en codigo. |
| Integracion Reddit | Media | Hay evidencia tecnica fuerte y estrategia clara, pero falta implementacion real del cliente del producto. |
| IA / evaluacion | Media-baja | Hay criterio y skill de integracion, pero el modulo esta vacio. |
| Persistencia | Baja | El modelo esta documentado, pero el store no esta implementado. |
| Delivery Telegram | Baja | El contrato de salida esta claro, pero el cliente no existe todavia. |
| Testing | Muy baja | Solo hay estructura de carpetas. |

### Lectura correcta de la madurez

Este repo es, ahora mismo, mas un sistema de decision y diseno que un producto ejecutable completo.

Eso tiene una ventaja enorme para un TFM: permite explicar muy bien el paso de idea -> discovery -> decisiones -> arquitectura -> diseno tecnico -> implementacion futura.

---

## 5. Project map

### Mapa corto

```text
auto-reddit/
|- src/auto_reddit/        Codigo del producto, hoy mayormente scaffolded
|- docs/                   Fuente de verdad funcional y tecnica
|- openspec/               Planning SDD por changes
|- skills/                 Skills locales del repo para agentes de codigo
|- scripts/                Tooling de investigacion, no flujo de producto
|- tests/                  Estructura de tests aun vacia
|- TFM/                    Documentacion academica
|- AGENTS.md / CLAUDE.md   Reglas operativas para agentes
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
- `contrato`: estructura de datos compartida entre modulos; aqui se preve con Pydantic
- `DTO/modelo de transferencia`: objeto orientado a mover datos entre capas
- `fallback`: cadena de respaldo cuando falla un proveedor principal
- `TTL`: tiempo de vida de un registro; aqui se piensa como `created_at + 7 dias`
- `scaffolding`: estructura inicial preparada pero aun sin implementacion real

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

Contenido real verificado: una sola docstring.

Rol esperado: orquestador del proceso diario.

Rol actual: placeholder arquitectonico.

Esto es importante: el archivo ya dice quien deberia ser, pero aun no hace ese trabajo.

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

Hoy contiene solo comentarios y ejemplos de futuros modelos.

Rol esperado: ser el idioma comun del sistema.

Rol actual: placeholder de contratos.

Esto es mas importante de lo que parece. En una arquitectura modular, `shared/contracts.py` es el sitio donde se convierten las decisiones abstractas en formas de datos concretas. Mientras este archivo siga vacio, la arquitectura todavia no tiene costuras reales.

#### `src/auto_reddit/reddit/client.py`

Contenido real verificado: una docstring.

Rol esperado:

- conectar con las APIs de Reddit
- traer posts y comentarios
- normalizar al contrato compartido

Rol actual: placeholder del adaptador de entrada principal.

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

Contenido real verificado: una docstring que menciona SQLite, TTL y un modelo de 3 estados.

Rol esperado: memoria operativa minima.

Rol actual: placeholder.

**Inconsistencia relevante:** la docstring habla de "modelo de 3 estados", mientras la arquitectura y el producto vigentes ya consolidan un modelo minimo donde los estados operativos relevantes documentados son `sent` y `rejected`, sin `approved`. Esto sugiere que `store.py` quedo atras respecto a la documentacion actual.

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

Solo contiene paquetes vacios.

Rol actual: estructura prevista.

Leccion importante: tener carpeta de tests no es tener testing. El repo todavia no tiene cobertura efectiva.

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

### 11.2 Flujo del change 1 ya especificado

El change `reddit-candidate-collection` tiene un flujo mas acotado:

1. probar `reddit3`
2. si falla, probar `reddit34`
3. si falla, probar `reddapi`
4. normalizar posts a `RedditCandidate`
5. filtrar a 7 dias
6. ordenar por recencia
7. devolver la lista completa, sin recorte a 8 y sin comentarios

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

### 11.5 Flujo actualmente ejecutable del producto si lo lanzaras hoy

Si ejecutaras `python -m auto_reddit.main`, con lo verificable ahora mismo, NO tendrias el pipeline funcional completo.

Lo honesto es decirlo asi:

- el entrypoint existe
- la arquitectura prevista existe
- pero el comportamiento de negocio aun no esta implementado en `src/auto_reddit/`

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

### 14.1 Implementacion funcional del pipeline

La gran pendiente obvia: los modulos del producto aun no estan implementados.

### 14.2 Parametros exactos de paginacion en todos los proveedores

El propio design del change 1 deja una pregunta abierta: como se solicita pagina 2+ en algunos proveedores aunque se vea el `cursor` en los raws.

### 14.3 Modelo final de persistencia materializado

La documentacion vigente apunta a memoria operativa minima, pero el store concreto aun no existe.

### 14.4 Contratos reales de evaluacion IA

Hay ejemplos conceptuales en `shared/contracts.py` y en la skill de DeepSeek, pero no un contrato productivo cerrado ya implementado.

### 14.5 Formato final de mensajes Telegram en codigo

El documento de producto lo define, pero el modulo de delivery aun no lo materializa.

### 14.6 Observabilidad real del sistema en ejecucion

La arquitectura habla de stdout con contadores y errores, pero todavia no hay logging real en el pipeline del producto.

### 14.7 Contradicciones historicas que conviene limpiar en el futuro

Hay restos documentales o placeholders que todavia reflejan estados anteriores:

- defaults 10/10 en `src/auto_reddit/config/settings.py`
- referencia a 3 estados en `src/auto_reddit/persistence/store.py`
- entradas antiguas de `TFM/diario.md` con `approved`, 10/10 o formulaciones ya superadas

No es grave, pero si no se limpia con cuidado puede confundir a quien llegue nuevo.

---

## 15. Cierre: que es hoy auto-reddit de verdad

`auto-reddit` no es todavia un bot operativo completo. Es algo mas interesante desde el punto de vista docente: un proyecto con buena maduracion de problema, buena disciplina documental, una arquitectura razonable para su escala, investigacion tecnica reproducible de sus dependencias externas y un camino de implementacion muy visible gracias a OpenSpec.

Si tuviera que resumirlo para un tribunal o para un junior, lo diria asi:

> `auto-reddit` es un sistema de deteccion asistida de oportunidades en Reddit para Odoo que ya tiene bastante bien resuelto el que, el por que y el como deberia construirse, aunque todavia este materializando el codigo funcional de sus modulos principales.

Y eso importa, porque un buen proyecto no empieza cuando escribes mucho codigo. Empieza cuando dejas de improvisar.

---

## 16. Como mantener viva esta guia

Si esta guia quiere seguir siendo util cuando lleguen nuevas implementaciones, tiene que actualizarse con reglas claras y no a golpe de intuicion.

### 16.1 Jerarquia de verdad documental

Cuando haya contradicciones, actualiza la guia siguiendo este orden:

1. `docs/product/` para verdad funcional
2. `docs/architecture.md` y `docs/integrations/` para verdad tecnica
3. `openspec/` para el plan vigente por change
4. `src/` y `tests/` para implementacion real materializada
5. `TFM/diario.md` y notas historicas como contexto, nunca como fuente vigente por defecto

### 16.2 Regla editorial clave

Cada actualizacion debe distinguir SIEMPRE entre:

- **producto**: lo que `auto-reddit` hace o debe hacer
- **herramienta de trabajo**: lo que ayuda a pensar, documentar, analizar o programar
- **flujo declarado por el autor**: decisiones de proceso no demostrables solo con el repo

Si se mezclan esas tres capas, la guia pierde valor academico y tecnico.

### 16.3 Cuando actualizar cada bloque

- actualiza la seccion 4 cuando cambie el nivel de madurez real de un modulo
- actualiza la seccion 9 cuando entren o salgan tools, skills o reglas de agente que afecten al proceso
- actualiza la seccion 10 cuando un placeholder pase a tener implementacion real o aparezcan nuevos modulos
- actualiza la seccion 11 cuando un flujo previsto pase a ser un flujo ejecutable
- actualiza la seccion 12 cuando un riesgo cambie de estado o aparezca una mitigacion nueva
- actualiza la seccion 14 cuando una incognita quede resuelta o nazcan otras nuevas

### 16.4 Como anadir futuros changes SDD sin romper la guia

Cuando se implemente un nuevo change, no reescribas la guia completa. Haz esto:

1. anade el change al mapa de proceso de la seccion 9
2. refleja en la seccion 10 que archivos o modulos se materializaron
3. mueve en la seccion 11 lo que ya sea flujo ejecutable
4. revisa secciones 12 y 14 para cerrar riesgos y abrir nuevos pendientes

### 16.5 Que no hacer

- no copiar trozos enteros de `README.md`, `docs/` u `openspec/` si no aportan sintesis
- no presentar tooling del autor como si fuera parte obligatoria del runtime del producto
- no ocultar limites de verificacion: si algo no se pudo demostrar desde repo o fuente publica, debe etiquetarse
- no dejar convivir sin nota decisiones historicas y decisiones vigentes
