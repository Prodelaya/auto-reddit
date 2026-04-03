> **Material didáctico e histórico.** Este documento narra cómo se construyó el sistema, explica su arquitectura en profundidad y sirve como guía de aprendizaje. No es la fuente de verdad operativa del proyecto.
> La verdad operativa actual vive en [`docs/README.md`](../docs/README.md).

# Guía didáctica de auto-reddit

Esta guía usa `auto-reddit` como hilo conductor para enseñar ingeniería de software. No es un manual de onboarding ni una descripción del producto. Es una guía de aprendizaje construida sobre un proyecto real y terminado.

Como apoyo visual del proyecto, el repositorio incluye una presentación HTML en `TFM/presentacion.html`. Puede abrirse localmente desde ese fichero y, cuando el repositorio tenga GitHub Pages activo, su URL esperada será `https://prodelaya.github.io/auto-reddit/TFM/presentacion.html`.

Al terminar de leerla deberías ser capaz de:

- entender cómo se lee y navega un proyecto desconocido con criterio
- distinguir producto, arquitectura, contratos, implementación y tooling
- comprender cómo fluyen los datos por un sistema en capas
- ver qué decisiones de diseño importan y por qué
- leer tests y entender qué nos dicen del diseño
- reconocer trade-offs reales en lugar de respuestas genéricas
- entender cómo se trabaja con IA de forma disciplinada en un proyecto real

---

## Índice

1. [Propósito de esta guía y cómo leerla](#1-propósito-de-esta-guía-y-cómo-leerla)
2. [Qué es este proyecto en una frase](#2-qué-es-este-proyecto-en-una-frase)
3. [Qué problema resuelve y qué no hace](#3-qué-problema-resuelve-y-qué-no-hace)
4. [Visión global del sistema](#4-visión-global-del-sistema)
5. [Flujo completo end-to-end](#5-flujo-completo-end-to-end)
6. [Arquitectura por capas](#6-arquitectura-por-capas)
7. [Cómo está organizado el repositorio](#7-cómo-está-organizado-el-repositorio)
8. [Ruta recomendada de lectura del código](#8-ruta-recomendada-de-lectura-del-código)
9. [Explicación carpeta por carpeta](#9-explicación-carpeta-por-carpeta)
10. [Módulos clave: explicación en profundidad](#10-módulos-clave-explicación-en-profundidad)
11. [Contratos, tipos y validaciones](#11-contratos-tipos-y-validaciones)
12. [Dependencias externas y por qué están ahí](#12-dependencias-externas-y-por-qué-están-ahí)
13. [Manejo de errores, retries y robustez](#13-manejo-de-errores-retries-y-robustez)
14. [Persistencia y estado](#14-persistencia-y-estado)
15. [Integraciones externas](#15-integraciones-externas)
16. [Tests: qué cubren y qué enseñan del diseño](#16-tests-qué-cubren-y-qué-enseñan-del-diseño)
17. [Decisiones de diseño y trade-offs](#17-decisiones-de-diseño-y-trade-offs)
18. [Qué enseña este proyecto sobre desarrollo con IA](#18-qué-enseña-este-proyecto-sobre-desarrollo-con-ia)
19. [Errores de lectura comunes en juniors](#19-errores-de-lectura-comunes-en-juniors)
20. [Evolución histórica del proyecto](#20-evolución-histórica-del-proyecto)
21. [Glosario técnico](#21-glosario-técnico)
22. [Changelog editorial de esta guía](#22-changelog-editorial-de-esta-guía)
23. [Despliegue en servidor Ubuntu propio](#23-despliegue-en-servidor-ubuntu-propio)

---

## 1. Propósito de esta guía y cómo leerla

### Para qué sirve

Esta guía no describe el producto. Lo usa para enseñar.

El objetivo es que un desarrollador junior, sin conocer el repo de antemano, pueda:

- entender la arquitectura real del sistema
- saber en qué orden leer el código y por qué
- comprender qué decide cada módulo y qué no
- aprender a leer decisiones de diseño en el código real
- ver cómo se conectan las capas, los contratos y los tests

### Cómo leerla si eres junior

No hace falta leerla de una vez. La estructura está pensada para avanzar de afuera hacia adentro:

1. Secciones 2, 3 y 4: entiende el problema y la forma general del sistema antes de ver código
2. Secciones 5 y 6: entiende el flujo y las capas antes de ver archivos
3. Secciones 7, 8 y 9: aprende a navegar el repo con criterio
4. Sección 10: entra en profundidad en los módulos más importantes
5. Secciones 11-16: entiende los mecanismos transversales (contratos, errores, tests, persistencia)
6. Secciones 17 y 18: aprende del diseño y del proceso
7. Secciones 19 y 21: errores comunes y glosario técnico de referencia

### Una advertencia importante

No confundas complejidad aparente con complejidad real. El repo tiene muchas carpetas y documentación extensa, pero el sistema en sí es un pipeline de cinco pasos. Cuando entiendas esos cinco pasos, todo lo demás encaja.

---

## 2. Qué es este proyecto en una frase

`auto-reddit` es un sistema que cada día laborable recoge posts recientes de `r/Odoo`, filtra los ya procesados, pide a una IA que evalúe cuáles merecen respuesta y entrega los resultados al equipo humano por Telegram.

Nunca publica en Reddit. La IA propone; el humano decide.

### En una frase

No es un bot que publica. Es un sistema de vigilancia y preparación de oportunidades.

---

## 3. Qué problema resuelve y qué no hace

### El problema real

Monitorizar Reddit a mano para detectar conversaciones donde una empresa experta en Odoo podría aportar valor es repetitivo, consume tiempo, depende del criterio de quién lo haga ese día y es difícil de hacer con disciplina todos los días.

El proyecto resuelve exactamente eso: automatizar la detección y la preparación, dejando la decisión editorial y la publicación en manos humanas.

### Lo que sí hace

- Vigila `r/Odoo` dentro de una ventana configurable (por defecto 7 días)
- Filtra posts ya procesados con anterioridad para no repetir trabajo
- Evalúa con IA si un post merece respuesta y genera un borrador en dos idiomas
- Entrega los resultados por Telegram con reintentos y priorización inteligente
- Emite un resumen diario aunque no haya oportunidades ese día
- Persiste el estado para garantizar unicidad entre ejecuciones

### Lo que no hace

- No publica en Reddit de forma autónoma
- No sustituye el criterio editorial humano
- No es un sistema de social listening multi-red ni multi-subreddit
- No tiene backlog editorial ni interfaz de gestión
- No opera en fin de semana (hay un guard explícito en el código)

### Límites funcionales concretos

El flujo está ajustado a cuotas de APIs gratuitas:

- hasta 8 candidatos evaluados por día (`daily_review_limit`)
- hasta 8 oportunidades entregadas por día (`max_daily_opportunities`)
- los comentarios no se recogen durante la fase de colección; solo para los posts ya seleccionados aguas arriba
- el caso "post antiguo con actividad reciente" está fuera del alcance actual

Estos límites no son arbitrarios. Están documentados en `docs/integrations/reddit/api-strategy.md` con el análisis de cuota que los justifica.

---

## 4. Visión global del sistema

### El mapa mental antes de ver código

Antes de abrir ningún archivo, necesitas una imagen mental del sistema. Esta es la más simple que lo describe correctamente:

```
Reddit (r/Odoo)
      │
      ▼
  [Colección]          ← reddit/client.py
      │                   tres proveedores, fallback chain
      ▼
  [Filtrado]           ← persistence/store.py
      │                   excluir ya procesados
      ▼
  [Contexto]           ← reddit/comments.py
      │                   recuperar comentarios del hilo
      ▼
  [Evaluación IA]      ← evaluation/evaluator.py
      │                   DeepSeek decide y genera
      ▼
  [Persistencia]       ← persistence/store.py
      │                   guardar decisión
      ▼
  [Entrega]            ← delivery/
      │                   Telegram, retry-first
      ▼
  Equipo humano        ← publica o descarta
```

`main.py` es el director de orquesta. No contiene la lógica de negocio: conecta los pasos.

`shared/contracts.py` es el idioma común. Los módulos no se importan entre sí directamente; todos hablan a través de ese archivo.

### Principios de diseño visible en esa imagen

**Separación de responsabilidades**: cada bloque tiene un trabajo único y bien definido. El bloque de colección no decide si un post merece respuesta. El bloque de evaluación no sabe cómo funciona Telegram.

**Contratos explícitos**: la salida de cada paso tiene un tipo Pydantic definido. No hay diccionarios ambiguos pasando de módulo en módulo.

**Recuperabilidad**: si Telegram falla en la entrega, el resultado de la IA está guardado. En el próximo ciclo se reintenta sin volver a llamar a la IA.

**Human-in-the-loop**: el sistema no publica. Entrega al humano y para ahí.

---

## 5. Flujo completo end-to-end

Este flujo simplificado es fiel al comportamiento actual de `main.py` pero no es una copia literal: el código real añade logging intermedio, ordenación explícita por recencia tras el filtrado, y comentarios sobre qué significa cada fase. Léelo como una guía de comprensión, no como la fuente de verdad; para eso está `src/auto_reddit/main.py`.

```python
def run() -> None:
    # 0. Guard de fin de semana
    if datetime.date.today().weekday() >= 5:
        logger.info("Weekend — skipping pipeline")
        return

    # 1. Inicializar persistencia
    store = CandidateStore(settings.db_path)
    store.init_db()

    # 2. Colectar candidatos
    candidates = collect_candidates(settings)
    # → lista de RedditCandidate, ordenados por recencia

    # 3. Filtrar ya decididos y candidatos incompletos
    decided_ids = store.get_decided_post_ids()
    eligible = [
        c for c in candidates
        if c.post_id not in decided_ids and c.is_complete
    ]
    review_set = eligible[:settings.daily_review_limit]
    # → máximo 8 candidatos limpios y únicos

    # 4. Recuperar contexto de comentarios
    thread_contexts = fetch_thread_contexts(review_set, settings)
    # → dict[post_id, ThreadContext] con calidad graduada

    # 5. Evaluar con IA
    evaluation_results = evaluate_batch(thread_contexts, settings)
    # → lista de AcceptedOpportunity | RejectedPost

    # 6. Persistir decisiones
    for result in evaluation_results:
        if isinstance(result, AcceptedOpportunity):
            store.save_pending_delivery(result.post_id, result.model_dump_json())
        else:
            store.save_rejected(result.post_id)

    # 7. Entregar por Telegram
    report = deliver_daily(store, settings, reviewed_post_count=len(review_set))
    logger.info("Pipeline complete", extra={"report": report.model_dump()})
```

### Qué enseña este código a un junior

**Una función, cinco responsabilidades distintas.** Cada línea lógica llama a un módulo diferente. `main.py` no implementa nada; coordina todo. Si ves código de negocio aquí, es una señal de que algo está en el lugar equivocado.

**Los tipos importan.** `evaluate_batch` devuelve una lista que puede contener dos tipos distintos. El `isinstance()` del paso 6 es una decisión de diseño: fuerza a que el caller maneje explícitamente ambos casos. No hay un campo `accepted: bool` que se pueda ignorar sin consecuencias.

**El estado se escribe antes de entregar.** Los resultados de la IA se persisten en el paso 6. Si el paso 7 falla, los datos están guardados. El próximo ciclo puede reintentar sin re-evaluar.

**El guard de fin de semana está en el código, no en el cron.** Si cambias el cron, el sistema sigue sin ejecutarse en fin de semana. Eso es un principio de diseño: no externalizar invariantes del negocio a infraestructura.

---

## 6. Arquitectura por capas

### Las cinco capas del sistema

```
┌─────────────────────────────────────────┐
│              ORQUESTACIÓN               │  main.py
└───────────────────┬─────────────────────┘
                    │ llama a
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  INTEGRACIÓN │ │  DOMINIO │ │   ENTREGA    │
│  EXTERNA     │ │          │ │              │
│              │ │evaluator │ │  delivery/   │
│ reddit/      │ │          │ │  selector    │
│ client.py    │ └──────────┘ │  renderer    │
│ comments.py  │              │  telegram    │
└──────────────┘              └──────────────┘
        │                           │
        ▼                           ▼
┌───────────────────────────────────────────┐
│               CONTRATOS                   │  shared/contracts.py
│   RedditCandidate · ThreadContext         │
│   AcceptedOpportunity · RejectedPost      │
│   PostRecord · DeliveryReport             │
└───────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│              PERSISTENCIA               │  persistence/store.py
│           SQLite · 3 estados            │
└─────────────────────────────────────────┘
```

### Principio de dependencia

El principio rector del diseño es que los módulos no deben depender de la estructura interna de otros módulos. En la práctica, esto significa que `reddit/`, `evaluation/`, `delivery/` y `persistence/` importan de `shared/contracts.py` y de `config/settings.py`, pero no se importan entre sí directamente. `main.py` los conecta en tiempo de ejecución.

Esto no es una ley matemática que se cumpla en el 100% de los casos en cualquier proyecto: hay situaciones donde una dependencia directa entre módulos es razonable. El valor aquí es el principio: cada módulo depende del idioma común, no de la implementación del vecino. Si `reddit/client.py` dependiera de detalles internos de `evaluation/evaluator.py`, cualquier cambio en el evaluador rompería el cliente.

### Capa de integración vs capa de dominio

La capa de integración (`reddit/`) tiene una responsabilidad clara: absorber la heterogeneidad de las APIs externas y entregar contratos homogéneos. No decide. No evalúa. No persiste.

La capa de dominio (`evaluation/`) tiene otra responsabilidad clara: aplicar criterio inteligente a datos ya limpios. No sabe de dónde vienen los datos ni a dónde van.

Esta separación es el principio de diseño más importante del sistema. Cuando la fuente externa cambia, solo toca la integración. Cuando cambian las reglas de evaluación, solo toca el dominio.

---

## 7. Cómo está organizado el repositorio

```
auto-reddit/
├── src/auto_reddit/           ← el producto
│   ├── main.py                  orquestador del pipeline
│   ├── config/settings.py       configuración y secretos
│   ├── shared/contracts.py      contratos Pydantic (idioma común)
│   ├── reddit/
│   │   ├── client.py            colección de candidatos (posts)
│   │   ├── comments.py          extracción de contexto (comentarios)
│   │   └── _constants.py        URLs y hosts de APIs
│   ├── evaluation/
│   │   └── evaluator.py         evaluación IA con DeepSeek
│   ├── delivery/
│   │   ├── __init__.py          orquestador de entrega diaria
│   │   ├── selector.py          selección determinista con TTL
│   │   ├── renderer.py          renderizado HTML para Telegram
│   │   └── telegram.py          cliente Bot API Telegram
│   └── persistence/
│       └── store.py             CandidateStore SQLite
├── tests/                     ← 396 tests (4 skipped)
│   ├── conftest.py              defaults dummy para CI sin .env
│   ├── test_main.py             weekend guard, filtro is_complete
│   ├── test_import_smoke.py     todos los módulos importan sin error
│   ├── test_settings_govern_runtime.py   contratos documentales
│   ├── test_ci_workflow.py      CI YAML verificado
│   ├── test_infra_hardening.py  robustez de infraestructura
│   ├── test_reddit/             colección y comentarios
│   ├── test_evaluation/         evaluación IA y contratos
│   ├── test_delivery/           selector, renderer, telegram, deliver_daily
│   ├── test_persistence/        SQLite CRUD y estado
│   └── test_integration/        integración operacional y smoke live
├── docs/                      ← fuente de verdad funcional y técnica
│   ├── README.md                mapa de documentación (leer primero)
│   ├── architecture.md          decisiones arquitectónicas
│   ├── operations.md            runbook operativo
│   ├── product/
│   │   ├── product.md           qué hace el producto y sus reglas
│   │   └── ai-style.md          cómo debe comportarse la IA
│   └── integrations/reddit/     estrategia y análisis de APIs
├── openspec/                  ← artefactos SDD archivados
│   ├── specs/                   especificaciones canónicas
│   └── changes/archive/         13 changes completos
├── skills/                    ← instrucciones para agentes
├── scripts/                   ← herramientas de investigación
├── .github/workflows/ci.yml   ← GitHub Actions
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

### Mapa semántico: qué pregunta responde cada directorio

| Pregunta | Dónde buscar |
|---|---|
| ¿Qué hace el producto? | `docs/product/product.md` |
| ¿Cómo debe comportarse la IA? | `docs/product/ai-style.md` |
| ¿Cómo está organizado el sistema? | `docs/architecture.md` |
| ¿Qué APIs de Reddit usar? | `docs/integrations/reddit/api-strategy.md` |
| ¿Cómo se ejecuta? | `docs/operations.md` |
| ¿Cómo se construyó? | `openspec/changes/archive/` y `TFM/diario.md` |
| ¿Cuál es el código real? | `src/auto_reddit/` |
| ¿Cómo trabajan los agentes en este repo? | `AGENTS.md`, `CLAUDE.md`, `skills/` |

---

## 8. Ruta recomendada de lectura del código

Si llegas al repo por primera vez, este es el orden que maximiza la comprensión:

### Paso 1: entiende el problema antes de ver código

Lee primero:
- `README.md` (3 minutos)
- `docs/product/product.md` (10 minutos)
- `docs/architecture.md` (10 minutos)

Hasta aquí deberías poder responder: qué hace el sistema, qué no hace, y por qué está organizado como está.

### Paso 2: entiende los contratos antes de ver implementaciones

Lee:
- `src/auto_reddit/shared/contracts.py` completo

Este archivo es el vocabulario del sistema. Si no entiendes los tipos, no entenderás las implementaciones. Verás los modelos Pydantic que definen cómo viajan los datos de un módulo a otro.

### Paso 3: lee el orquestador

Lee:
- `src/auto_reddit/main.py`

Cinco pasos lógicos. Entiende cuál es la responsabilidad de cada llamada antes de entrar en cada módulo.

### Paso 4: entra en los módulos de afuera hacia adentro

En este orden:
1. `src/auto_reddit/reddit/client.py` — de dónde vienen los datos
2. `src/auto_reddit/reddit/comments.py` — cómo se enriquecen
3. `src/auto_reddit/evaluation/evaluator.py` — cómo se evalúan
4. `src/auto_reddit/persistence/store.py` — cómo se persisten
5. `src/auto_reddit/delivery/__init__.py` — cómo se entregan
6. `src/auto_reddit/delivery/selector.py`, `renderer.py`, `telegram.py` — los colaboradores

### Paso 5: lee los tests para entender el diseño

Para cada módulo que acabas de leer:
- `tests/test_reddit/test_client.py`
- `tests/test_reddit/test_comments.py`
- `tests/test_evaluation/test_evaluator.py`
- `tests/test_persistence/test_store.py`
- `tests/test_delivery/test_deliver_daily.py`
- `tests/test_integration/test_operational.py`

Los tests no son solo verificación. Son especificación ejecutable. Te dicen qué comportamiento es intencionado.

### Cómo leer un archivo de este repo

Cuando abras cualquier archivo de `src/auto_reddit/`, sigue este protocolo antes de leer línea por línea:

**1. Mira los imports**
Los imports te dicen de qué depende el módulo. Si importa de `shared/contracts.py`, trabaja con los contratos del pipeline. Si importa de `config/settings.py`, consume configuración. Si importa de `httpx` o `openai`, hace I/O externo.

**2. Identifica el punto de entrada público**
Las funciones sin prefijo `_` son la API del módulo. Las funciones con `_` son helpers privados. El punto de entrada público es lo que `main.py` llama directamente. Por ejemplo: `collect_candidates`, `fetch_thread_contexts`, `evaluate_batch`, `deliver_daily`.

**3. Lee la firma del punto de entrada**
La firma te dice qué recibe y qué devuelve. Antes de entender la implementación, entiende el contrato: `collect_candidates(settings: Settings) -> list[RedditCandidate]`.

**4. Separa los helpers del flujo principal**
Los helpers privados (funciones `_`) hacen una sola cosa: normalizar, paginar, construir mensajes, calcular TTL. El flujo principal los llama en orden. Léelos en el orden en que los llama el flujo, no en el orden en que aparecen en el archivo.

**5. Detecta los contratos de entrada y salida**
Fíjate en qué tipo Pydantic llega y qué tipo sale. Eso te dice el papel del módulo en el pipeline: adapta datos de entrada, transforma, persiste o entrega.

**6. Busca dónde se testea**
Cada módulo tiene su directorio de tests en `tests/`. Los tests concretan el comportamiento esperado mejor que cualquier comentario. Si hay algo que no entiendes en el código, busca el test correspondiente.

**7. Anota qué decisiones de diseño revela**
Pregúntate: ¿por qué esta función está separada? ¿por qué este campo es opcional? ¿por qué este orden de operaciones? La mayoría de las decisiones no-obvias tienen una razón que se explica en esta guía o en `docs/architecture.md`.

---

## 9. Explicación carpeta por carpeta

### `src/auto_reddit/`

El producto. Todo lo que ejecuta el pipeline vive aquí.

La razón del `src-layout` (código en `src/`, no en la raíz) es que evita problemas de importación durante los tests: fuerza que el código se instale como paquete antes de ser importado, en lugar de resolverse desde el directorio actual.

### `src/auto_reddit/config/`

Un solo archivo: `settings.py`. Define `Settings` con `pydantic-settings`, que lee variables de entorno (y opcionalmente de `.env`) con validación en tiempo de importación.

**Qué es importante aquí**: la instancia `settings = Settings()` se crea a nivel de módulo. Eso significa que si falta una variable obligatoria, el error ocurre al importar, no al ejecutar. Falla rápido, falla con claridad.

### `src/auto_reddit/shared/`

Un solo archivo: `contracts.py`. Define todos los modelos Pydantic del sistema.

**Por qué existe este módulo**: para que ningún módulo dependa de la estructura interna de otro. Si `evaluation/evaluator.py` necesita saber cómo es un `ThreadContext`, lo importa de `shared/`, no de `reddit/comments.py`. Esa indirección parece burocracia al principio; se agradece cuando hay que cambiar algo.

### `src/auto_reddit/reddit/`

Dos archivos de lógica (`client.py`, `comments.py`) más uno de constantes (`_constants.py`).

`client.py` recolecta posts. `comments.py` recolecta comentarios para posts ya seleccionados. Ambos tienen la misma arquitectura interna: normalizers por proveedor, fallback chain, retry.

La razón de tenerlos separados es que los comentarios solo se piden después de que el filtrado ya redujo la lista. Si los pidieras en la colección inicial, gastarías cuota en posts que luego se filtran.

### `src/auto_reddit/evaluation/`

Un solo archivo: `evaluator.py`. Conecta con DeepSeek vía el SDK de OpenAI, envía el system prompt y el contexto del hilo, valida la respuesta con Pydantic y construye el resultado final.

Este es el módulo más complejo del sistema. El system prompt es estático y extenso (~280 líneas). La razón de un prompt largo y explícito es que la ambigüedad en las instrucciones produce comportamiento impredecible en el modelo.

### `src/auto_reddit/persistence/`

Un solo archivo: `store.py`. Define `CandidateStore`, que gestiona la tabla SQLite `post_decisions`.

**Qué hace**: recuerda qué posts ya fueron procesados para no repetirlos. Guarda el resultado de la IA para poder reintentar la entrega sin volver a llamarla.

### `src/auto_reddit/delivery/`

Cuatro archivos con responsabilidades separadas:

- `__init__.py` — orquestador: conecta selector, renderer y telegram
- `selector.py` — decide qué entregar hoy: reintentos primero, luego nuevos, con TTL y cap
- `renderer.py` — formatea mensajes HTML para Telegram
- `telegram.py` — cliente mínimo de la Bot API

La separación aquí es especialmente limpia: el selector no sabe de Telegram, el renderer no sabe de SQLite, el cliente de Telegram no sabe de negocio.

### `tests/`

396 tests organizados por módulo más tests transversales. La estructura espeja `src/`: hay un directorio de tests por módulo de producción.

Los tests más instructivos para aprender del diseño son los de integración en `test_integration/test_operational.py`. No prueban funciones aisladas; prueban que las fases del pipeline no interfieren entre sí.

### `docs/`

Fuente de verdad funcional y técnica. `docs/README.md` actúa como mapa: te dice qué documento responde cada tipo de pregunta.

Regla importante: si hay contradicción entre `docs/` y `src/`, el código manda. Pero en este proyecto los dos están deliberadamente alineados.

### `openspec/`

Artefactos del proceso de construcción. Cada change tiene su carpeta en `openspec/changes/archive/` con discovery, proposal, spec, design, tasks y verify.

No es código de producción. Es la trazabilidad de cómo se construyó el sistema. Para un junior es valiosísimo porque muestra que los sistemas no nacen completos: se construyen paso a paso con criterio.

### `scripts/`

Herramientas de investigación, no de producto. `scripts/reddit_api_raw_snapshot.py` llama a los endpoints de las APIs de Reddit y guarda los JSON crudos en `docs/integrations/reddit/*/raw/`. Existió para reducir incertidumbre antes de codificar los normalizers.

**Lección**: antes de escribir un adaptador para una API externa, captura evidencia reproducible de qué devuelve esa API. No asumas. No confíes solo en la documentación.

---

## 10. Módulos clave: explicación en profundidad

### `shared/contracts.py` — el idioma del sistema

Es el archivo más importante para entender el sistema. Antes de leer cualquier otra implementación, lee este.

**Por qué los contratos importan tanto en este sistema**

Las APIs de Reddit devuelven estructuras diferentes según el proveedor. DeepSeek devuelve un JSON con decenas de campos. Telegram espera texto formateado. Sin contratos explícitos, cada módulo inventaría su propia representación de los datos y el sistema entero sería frágil.

Los contratos Pydantic hacen tres cosas:
1. Validan que los datos tienen la forma esperada
2. Documentan el "idioma" de cada paso del pipeline
3. Fuerzan decisiones explícitas sobre campos opcionales

**La cadena de tipos del pipeline**

```
Reddit API (heterogéneo)
    │ normalizer por proveedor
    ▼
RedditCandidate          ← contrato de colección
    │ + recuperar comentarios
    ▼
ThreadContext            ← contrato de contexto
    │ + evaluar IA
    ▼
AIRawResponse            ← respuesta bruta del modelo
    │ + enriquecer con datos del pipeline
    ▼
AcceptedOpportunity      ← contrato de oportunidad aceptada
RejectedPost             ← contrato de post rechazado
    │ + persistir
    ▼
PostRecord               ← contrato de registro SQLite
    │ + entregar
    ▼
DeliveryReport           ← contrato de informe de entrega
```

Cada paso transforma un tipo en otro. Los módulos no comparten estado interno; se comunican exclusivamente a través de estos tipos.

**Diseño de `AcceptedOpportunity`: qué genera la IA y qué no**

```python
class AcceptedOpportunity(BaseModel):
    # Estos campos los construye el pipeline, nunca la IA:
    post_id: str
    title: str
    link: str

    # Estos campos los genera la IA:
    post_language: str
    opportunity_type: OpportunityType
    opportunity_reason: str
    post_summary_es: str
    comment_summary_es: str | None = None
    suggested_response_es: str
    suggested_response_en: str
    warning: str | None = None
    human_review_bullets: list[str] | None = None
```

`post_id`, `title` y `link` nunca se le piden a la IA. La razón es que estos campos son deterministas: el pipeline ya los conoce. Pedírselos a la IA introduce riesgo de alucinación donde no hace falta. Esta decisión de diseño es sutil pero importante: la IA solo genera lo que requiere razonamiento.

**El estado de `pending_delivery`: por qué existe**

```python
class PostDecision(str, Enum):
    sent = "sent"                         # entregado — decisión final
    rejected = "rejected"                 # rechazado — decisión final
    pending_delivery = "pending_delivery" # IA aceptó, Telegram pendiente
```

`pending_delivery` existe para desacoplar la decisión de la IA de la confirmación de Telegram. Si Telegram falla en la entrega, el resultado de la IA está guardado en `opportunity_data`. El próximo ciclo reintenta la entrega sin volver a llamar a DeepSeek. Sin ese estado intermedio, un fallo de red causaría re-evaluación innecesaria y posiblemente cambio de decisión.

---

### `reddit/client.py` — la capa de integración más compleja

Este archivo tiene ~350 líneas. Recolecta posts de `r/Odoo` usando tres proveedores distintos con fallback.

**Estructura interna por responsabilidades**

```
collect_candidates(settings)          ← punto de entrada público
    │
    ├── Intenta reddit3
    │       _paginate(reddit3, ...)
    │           _fetch_with_retry(url, headers) → JSON crudo
    │           _normalize_reddit3(json) → [RedditCandidate]
    │           _cursor_reddit3(json) → cursor o None
    │
    ├── Si falla → Intenta reddit34
    │       _paginate(reddit34, ...)
    │           _fetch_with_retry(url, headers) → JSON crudo
    │           _normalize_reddit34(json) → [RedditCandidate]
    │           _cursor_reddit34(json) → cursor o None
    │
    ├── Si falla → Intenta reddapi
    │       _paginate(reddapi, ...)
    │           _fetch_with_retry(url, headers) → JSON crudo
    │           _normalize_reddapi(json) → [RedditCandidate]
    │           _cursor_reddapi(json) → cursor o None
    │
    └── Sobre el resultado del proveedor ganador:
            filtrar por review_window_days
            filtrar subreddit == "odoo"
            ordenar por created_utc descendente
            devolver lista
```

**Tres patrones de diseño que conviene aprender aquí**

*Normalizers separados por proveedor*

Cada API tiene una estructura distinta. `reddit3` devuelve posts en `body.body[]`, `reddit34` en `data.posts[].data`, `reddapi` en `posts[].data`. En lugar de un gran `if/elif/else` en el código principal, hay una función normalizer por proveedor. El código principal llama al normalizer correcto y no sabe nada de las diferencias.

Este patrón se llama adaptador. Es uno de los más útiles en sistemas que integran fuentes heterogéneas.

*Cursor extractors separados*

La paginación también difiere por proveedor. El cursor está en `response.meta.cursor` en reddit3, en `response.data.cursor` en reddit34, en `response.cursor` en reddapi. En lugar de condicionales en el bucle de paginación, hay un extractor por proveedor. El bucle genérico `_paginate` recibe una función y la llama.

*Fallback whole-step*

Si un proveedor falla en cualquier punto del proceso (no solo en la primera llamada), se descarta entero y se intenta el siguiente. No hay fallback parcial por página. Esta decisión evita resultados mezclados que serían difíciles de normalizar consistentemente.

**Por qué los órdenes de fallback son distintos para posts y comentarios**

Posts: `reddit3 → reddit34 → reddapi`
Comentarios: `reddit34 → reddit3 → reddapi`

Para comentarios, `reddit34` es el proveedor primario porque ofrece `sort=new` (recientes primero), timestamps precisos, `parent_id` y árbol de replies anidado. Para posts, `reddit3` es primario porque ofrece una colección más amplia y paginación más estable.

La calidad del contexto de comentarios importa más que la calidad de la lista de posts, porque el sistema de evaluación IA depende directamente de entender la conversación. Por eso se optimiza primero el proveedor de comentarios.

**`ContextQuality`: haciendo visible la calidad del contexto**

```python
class ContextQuality(str, Enum):
    full     = "full"      # reddit34: árbol, timestamps, sort=new garantizado
    partial  = "partial"   # reddit3: árbol recursivo, sin depth/parent_id
    degraded = "degraded"  # reddapi: solo top comments, plano, sin timestamps
```

Este enum no es solo documentación. El evaluador IA lo lee y ajusta su comportamiento: con calidad `degraded`, añade un aviso explícito en el prompt al modelo y genera campos `warning` y `human_review_bullets` en la respuesta.

---

### `evaluation/evaluator.py` — la capa de dominio

Este es el módulo más complejo del sistema. Su trabajo: recibir un `ThreadContext` y devolver un `AcceptedOpportunity` o un `RejectedPost`.

**Arquitectura interna**

```python
evaluate_batch(thread_contexts, settings)
    │ itera cada post
    ▼
_evaluate_single(ctx, client, model)   ← con retry tenacity
    │
    ▼
_evaluate_single_raw(ctx, client, model)
    ├── _build_system_prompt()         ← estático, cacheable
    ├── _build_user_message(ctx)       ← determinista por post
    │
    ├── llamada DeepSeek con structured output
    │
    ├── validar AIRawResponse (Pydantic)
    │
    └── construir AcceptedOpportunity / RejectedPost
```

**El system prompt: por qué es tan largo**

El system prompt tiene ~280 líneas. Esto no es exceso; es precisión.

Un prompt corto y ambiguo delega decisiones al modelo. Un prompt largo y explícito fija el comportamiento esperado. En este caso el prompt define:

- El rol: "evaluador con sesgo por defecto hacia NO intervenir"
- El proceso obligatorio: DECIDE primero, luego GENERA. Este orden evita que el modelo escriba una respuesta plausible y luego racionalice la aceptación.
- La regla de abstención: solo ACEPTA si hay evidencia clara + contribución útil posible
- Los tipos cerrados de oportunidad (cuatro valores exactos)
- Los tipos cerrados de rechazo (cuatro valores exactos)
- Las reglas editoriales: no inventar rutas de menú, no defender Odoo por reflejo, distinguir hipótesis de hechos
- El checklist técnico de Odoo: productos, multi-empresa, contabilidad, OCR, OCA, etc.
- La política de idioma: sumarios en español, respuestas en español y en inglés

La longitud del prompt es proporcional a la precisión del comportamiento esperado. Cuando el modelo tiene que inferir las reglas, las infiere de forma inconsistente. Cuando las tiene explícitas, las sigue.

**Structured output y validación Pydantic**

DeepSeek devuelve un JSON que se valida contra `AIRawResponse`. Si la validación falla (campo faltante, tipo incorrecto, valor fuera del enum cerrado), el post se salta sin abortar el batch.

Esta estrategia tiene consecuencias importantes: un fallo de validación no cuenta como rechazo, no se persiste en SQLite y no reduce el cap diario. Es como si el post no hubiera pasado por el evaluador. Eso puede causar que el mismo post vuelva a evaluarse en el próximo ciclo.

La alternativa sería marcar el post como rechazado con un tipo de error. Eso sería más conservador pero consumiría la "ranura" de rechazo para algo que es un fallo técnico, no una decisión de negocio. El sistema elige no contaminar el modelo de estados con errores transitorios.

---

### `persistence/store.py` — la memoria operativa mínima

`CandidateStore` es una clase que envuelve SQLite con la API mínima necesaria para el pipeline.

**El esquema**

```sql
CREATE TABLE post_decisions (
    post_id          TEXT PRIMARY KEY,
    status           TEXT NOT NULL,
    opportunity_data TEXT,
    decided_at       INTEGER NOT NULL
)
```

Tres columnas y un índice. El sistema completo vive en esa tabla.

**Por qué `get_decided_post_ids` no devuelve `pending_delivery`**

```python
def get_decided_post_ids(self) -> set[str]:
    cursor.execute(
        "SELECT post_id FROM post_decisions WHERE status IN (?, ?)",
        ("sent", "rejected")
    )
```

Los posts `pending_delivery` no están en el conjunto de "ya decididos". Eso es intencional: un post en `pending_delivery` debe seguir siendo elegible para reintento de entrega. Si lo incluyeras en los decididos, bloquearías el reintento y perderías la oportunidad.

Esta distinción entre "ya procesado por la IA" y "ya entregado al equipo" es el corazón del modelo de estados.

**Operaciones idempotentes con upsert**

Todos los métodos de escritura usan `INSERT ... ON CONFLICT DO UPDATE`:

```python
cursor.execute(
    """
    INSERT INTO post_decisions (post_id, status, decided_at)
    VALUES (?, ?, ?)
    ON CONFLICT(post_id) DO UPDATE SET status=excluded.status
    """,
    (post_id, "rejected", int(time.time()))
)
```

Idempotente significa que ejecutar la operación dos veces produce el mismo resultado que ejecutarla una. Eso importa porque en sistemas con reintentos, las mismas operaciones pueden ejecutarse más de una vez.

**Bug real encontrado y corregido: `decided_at` y el TTL**

En la versión inicial, `save_pending_delivery` sobreescribía `decided_at` en cada reintento. El resultado: el TTL (tiempo de vida del registro) se recalculaba desde el último intento, no desde la decisión original de la IA. Un post evaluado el lunes que fallaba en Telegram el martes y se reintentaba el jueves tendría su TTL calculado desde el jueves.

La corrección: el upsert de `save_pending_delivery` preserva `decided_at` original en reintentos usando `DO UPDATE SET ... decided_at=CASE WHEN ...`. El test de regresión añadido verifica exactamente este comportamiento.

Esta es una lección importante: algunos bugs no son errores de lógica obvia. Son errores de semántica, donde el código "funciona" pero hace algo diferente a lo que pretende.

---

### `delivery/__init__.py` — orquestador de entrega

`deliver_daily` es la función que conecta los tres colaboradores del módulo delivery.

**Flujo interno**

```python
def deliver_daily(store, settings, *, reviewed_post_count=None, now_utc=None):
    now = now_utc or datetime.datetime.now(datetime.timezone.utc)

    # 1. Obtener todos los pending_delivery
    pending = store.get_pending_deliveries()

    # 2. Seleccionar qué entregar hoy (retry-first, cap, TTL)
    selected, expired_ids = select_deliveries(pending, now, cap=settings.max_daily_opportunities)

    # 3. Enviar cada oportunidad
    sent_ok = sent_failed = 0
    for record in selected:
        opp = AcceptedOpportunity.model_validate_json(record.opportunity_data)
        html = render_opportunity(opp)
        ok = send_message(settings.telegram_bot_token, settings.telegram_chat_id, html)
        if ok:
            store.mark_sent(record.post_id)
            sent_ok += 1
        else:
            sent_failed += 1

    # 4. Enviar resumen (no bloqueante)
    summary_html = render_summary(len(selected), retries=..., new=..., ...)
    summary_ok = send_message(settings.telegram_bot_token, settings.telegram_chat_id, summary_html)

    # 5. Purgar expirados
    store.purge_expired(expired_ids)

    return DeliveryReport(...)
```

**Principio: `sent` solo se escribe tras confirmación**

`store.mark_sent(record.post_id)` se llama dentro del `if ok:`. Si Telegram responde con un error, el post sigue en `pending_delivery`. Esto es intencional: la transición al estado final `sent` requiere confirmación explícita de la entrega.

Un bug aquí sería escribir `mark_sent` antes del `if ok:`. El post quedaría marcado como enviado aunque no hubiera llegado al equipo. Es un error de orden de operaciones, no de lógica.

**El resumen se envía siempre, incluso con 0 oportunidades**

Esto responde a un requisito del producto: el equipo recibe confirmación todos los días laborables de que el sistema corrió, aunque no haya nada que entregar. Si no llega resumen, algo falló. El silencio del sistema es ruido, no señal.

---

### `delivery/selector.py` — selección determinista

`select_deliveries` decide qué entregar cada día. Su comportamiento es determinista dado el mismo conjunto de registros y el mismo timestamp.

**Algoritmo**

```python
def select_deliveries(records, now, cap=8):
    # 1. Filtrar registros sin opportunity_data
    # 2. Filtrar registros con JSON malformado (no cuentan para el cap)
    # 3. Separar expirados (TTL < now) de válidos
    # 4. Entre válidos, separar reintentos (decided_at anterior a hoy) de nuevos
    # 5. Ordenar reintentos por decided_at ASC (más antiguos primero)
    # 6. Ordenar nuevos por decided_at ASC
    # 7. Reintentos primero, luego nuevos, hasta llenar el cap
```

**Retry-first: por qué los reintentos tienen prioridad**

Un post que fue evaluado y aceptado ayer pero no se pudo entregar por un fallo de Telegram tiene más urgencia que un post evaluado hoy. La política retry-first maximiza la probabilidad de que una oportunidad detectada llegue al equipo.

**TTL: tiempo de vida de `pending_delivery`**

Los registros `pending_delivery` tienen fecha de caducidad. La regla:
- Decidido lunes-miércoles → expira el viernes a las 23:59:59 UTC
- Decidido jueves-domingo → expira el próximo lunes a las 23:59:59 UTC

La lógica: una oportunidad de este lunes sigue siendo relevante hasta el fin de la semana laboral. Pero si no se entrega antes del viernes, la siguiente semana laboral empieza con una pizarra limpia.

Los registros expirados no se incluyen en el conjunto entregable. Se purgan de SQLite al final del ciclo.

---

## 11. Contratos, tipos y validaciones

### Por qué Pydantic y no diccionarios

Pydantic valida en tiempo de construcción. Si intentas crear un `RedditCandidate` con un `post_id` que es `None`, Pydantic lanza `ValidationError` inmediatamente. Con diccionarios, ese error aparecería más tarde (o nunca, como un bug silencioso).

Además, los modelos Pydantic son documentación ejecutable. Leer `RedditCandidate` te dice exactamente qué campos existen, cuáles son opcionales y cuáles tienen valores por defecto.

### `is_complete`: un computed field

`is_complete` es `True` solo cuando el candidato tiene todos los campos que el pipeline necesita para evaluarlo y persistirlo correctamente. Según el código actual de `shared/contracts.py`:

```python
@computed_field
@property
def is_complete(self) -> bool:
    """True only when ALL minimum-contract fields are present and non-empty.

    Minimum contract: post_id, title, url, permalink, subreddit,
    created_utc (non-zero), source_api, selftext (not None), author (not None).
    Fields deliberately optional (num_comments) do NOT affect completeness.
    """
    return bool(
        self.post_id
        and self.title
        and self.url
        and self.permalink
        and self.subreddit
        and self.created_utc      # 0 means unknown → incomplete
        and self.source_api
        and self.selftext is not None
        and self.author is not None
    )
```

El punto que puede sorprender: `selftext` y `author` son campos **opcionales** en el modelo (admiten `None`), pero afectan a `is_complete`. Un candidato donde el autor no se pudo determinar, o donde el cuerpo del post llegó como `None`, se considera incompleto. La razón: un post sin cuerpo ni autor proporciona contexto insuficiente para que la IA evalúe si merece respuesta.

`num_comments` es la excepción deliberada: no forma parte del contrato mínimo porque su ausencia no impide la evaluación.

Un candidato incompleto no se descarta durante la colección. Se conserva con `is_complete=False` y se filtra antes de la evaluación IA. El filtro vive en `main.py`. Esta decisión de diseño mantiene la colección agnóstica sobre los requisitos del evaluador: si mañana el evaluador necesita menos campos, el filtro cambia en un solo punto.

### Enums cerrados: por qué importan

`OpportunityType` y `RejectionType` son enums cerrados:

```python
class OpportunityType(str, Enum):
    funcionalidad = "funcionalidad"
    desarrollo = "desarrollo"
    dudas_si_merece_la_pena = "dudas_si_merece_la_pena"
    comparativas = "comparativas"
```

Si la IA devuelve un valor que no está en el enum, Pydantic lanza `ValidationError` y el post se salta. Esto es intencional. La alternativa sería aceptar cualquier string y dejar que el sistema procese tipos no definidos, lo que rompería las lógicas downstream que dependen de valores conocidos.

Un enum cerrado es un contrato: "el sistema solo entiende estos valores". Cualquier otra cosa es un error de integración.

### `EvaluationResult`: unión discriminada

```python
EvaluationResult = Annotated[Union[AcceptedOpportunity, RejectedPost], ...]
```

El caller usa `isinstance()` para distinguir casos:

```python
for result in evaluation_results:
    if isinstance(result, AcceptedOpportunity):
        store.save_pending_delivery(...)
    else:
        store.save_rejected(...)
```

Este patrón fuerza el manejo explícito de ambos casos. Sin él, un `result.post_id` funcionaría en ambos (ambos tienen ese campo) pero `result.opportunity_type` lanzaría `AttributeError` en los rechazos. La unión discriminada hace que el compilador de tipos (o los tests) capten ese error antes de llegar a producción.

---

## 12. Dependencias externas y por qué están ahí

### `pydantic` y `pydantic-settings`

Pydantic valida datos en tiempo de construcción y genera modelos con documentación implícita. `pydantic-settings` extiende eso a la configuración: lee variables de entorno, valida tipos y falla rápido si falta algo obligatorio.

Alternativa que no se usa: `dataclasses` + validación manual. Se descarta porque es más verboso y la validación hay que escribirla a mano.

### `openai` SDK

DeepSeek expone una API compatible con la API de OpenAI. El proyecto usa el SDK de OpenAI para conectar con DeepSeek simplemente cambiando la `base_url`. Esto evita escribir un cliente HTTP a mano para una API ya documentada y con SDK maduro.

La clave para entender esta decisión: el sistema no usa ChatGPT, pero aprovecha el estándar de API que OpenAI popularizó. Muchos proveedores de modelos adoptaron ese estándar para facilitar la migración.

### `httpx`

Cliente HTTP con soporte nativo para async, context managers y retry-friendly. Se usa para las llamadas a las APIs de Reddit. Alternativa obvia: `requests`. Se elige `httpx` porque es la evolución moderna y tiene mejor soporte para el modelo de I/O que usa el sistema.

### `tenacity`

Reintentos declarativos con decoradores:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def _evaluate_single_raw(...):
    ...
```

Alternativa: bucles `while` con `time.sleep`. Se descarta porque mezcla la lógica de negocio con la lógica de retry, hace el código más difícil de leer y los tests más difíciles de escribir. Con `tenacity`, el retry es una anotación separable de la lógica.

### Stack de Python y herramientas

**Python 3.14**: La versión más reciente del lenguaje. En un proyecto educativo y en desarrollo, usar la versión más reciente es apropiado.

**uv**: gestor de paquetes y entornos virtuales de nueva generación. Más rápido que `pip` + `venv`, con lockfile reproducible (`uv.lock`) y gestión integrada de versiones de Python.

**Docker**: el sistema se ejecuta como contenedor efímero. Ver sección 17.3 para el razonamiento.

**SQLite**: base de datos integrada en Python. No requiere proceso separado, no tiene configuración de red, es suficiente para un pipeline de un solo proceso por día. Ver sección 14.

---

## 13. Manejo de errores, retries y robustez

### Estrategia general: errores transitorios vs permanentes

El sistema distingue dos tipos de errores:

**Transitorios**: problemas de red, rate limits, timeouts. Se retribuyen con backoff exponencial. Ejemplo: `APIError` de DeepSeek.

**Permanentes**: validación fallida, JSON malformado, error de tipo. Se saltan sin reintentar. Ejemplo: `ValidationError` de Pydantic al parsear la respuesta IA.

```python
try:
    return _evaluate_single_raw(ctx, client, model)
except (ValidationError, JSONDecodeError, ValueError) as exc:
    logger.warning("Permanent error for post %s: %s", ctx.candidate.post_id, exc)
    return None  # el post se salta, no se aborta el batch
except Exception as exc:
    # reraise para tenacity
    raise
```

### Robustez en la colección de candidatos

Si un proveedor de Reddit falla completamente, se intenta el siguiente. Si todos fallan, `collect_candidates` devuelve lista vacía y loguea el error. El pipeline continúa con 0 candidatos (lo cual produce un resumen diario con "0 posts revisados").

Este comportamiento es intencional: un fallo de la API de Reddit no debe derribar el pipeline. El sistema degrada limpiamente.

### Robustez en la extracción de comentarios

Si todos los proveedores fallan para un post específico, ese post se descarta del diccionario de contextos. El resto del batch sigue. Un post sin contexto de comentarios no bloquea la evaluación de los demás.

### Robustez en la entrega Telegram

Tenacity reintenta hasta 3 veces con backoff (2s–10s) ante `HTTPError`. Si falla después de los reintentos, `send_message` devuelve `False`. El orquestador registra el fallo pero no aborta. Los demás mensajes se intentan.

El resumen diario se envía después de los mensajes individuales y se trata como no bloqueante: si falla, los mensajes individuales ya están enviados.

### El principio de "no contaminar el estado con errores transitorios"

Un post que falla la validación Pydantic de la respuesta IA no se marca como `rejected`. Queda sin estado, lo que significa que volverá a entrar al pipeline al día siguiente.

Podría parecer un bug, pero es una decisión de diseño. Marcar como `rejected` algo que no es realmente un rechazo de negocio distorsionaría las métricas y ocuparía espacio en el cap diario. Un error de validación es una anomalía técnica, no una decisión editorial.

---

## 14. Persistencia y estado

### Por qué SQLite y no algo más

El sistema ejecuta una vez al día. Un solo proceso. Sin concurrencia. La persistencia necesaria es mínima: recordar qué posts ya se procesaron.

SQLite es suficiente para eso. No requiere configuración, no tiene proceso separado, el archivo de base de datos puede vivir en un volumen Docker, y Python trae soporte nativo.

La decisión de no usar PostgreSQL, MySQL o cualquier otro servidor de base de datos no es descuido. Es apropiada para la escala y el modelo operativo del sistema.

### El modelo de tres estados

```
          ┌─────────────┐
          │   pipeline  │
          │   (nuevo)   │
          └──────┬──────┘
                 │
    ┌────────────┴────────────┐
    │ IA acepta               │ IA rechaza
    ▼                         ▼
pending_delivery         rejected (final)
    │
    │ Telegram confirma
    ▼
  sent (final)
```

`sent` y `rejected` son estados finales: un post en esos estados no vuelve a entrar al pipeline.

`pending_delivery` es transitorio: un post en este estado puede reintentarse en la entrega. También puede expirar por TTL.

### El TTL de `pending_delivery`

Los registros `pending_delivery` caducan al final de la semana laboral. La regla concreta:
- Decidido lunes a miércoles → expira el viernes a las 23:59:59 UTC
- Decidido jueves a domingo → expira el siguiente lunes a las 23:59:59 UTC

Un post evaluado y aceptado el jueves que no se pudo entregar el viernes expira el siguiente lunes, no el viernes. Eso da la semana laboral siguiente como ventana de reintento antes de considerarlo irrelevante.

### El contrato de despliegue: `DB_PATH`

```
# docker-compose.yml
services:
  auto-reddit:
    volumes:
      - sqlite_data:/data
    environment:
      DB_PATH: /data/auto_reddit.db
```

Este detalle es crítico. Si `DB_PATH` no apunta al volumen montado, SQLite escribe en la capa efímera del contenedor. El sistema "funciona" sin error: arranca, ejecuta, termina. Pero la próxima ejecución empieza con una base de datos vacía. Todos los posts procesados ayer son desconocidos hoy.

El bug es silencioso: no hay error, no hay advertencia. Solo comportamiento incorrecto. La lección para un junior: los contratos de despliegue (qué configuración es necesaria en producción) son parte del sistema, no un detalle operativo secundario.

---

## 15. Integraciones externas

### Reddit — tres proveedores vía RapidAPI

El sistema usa tres APIs no oficiales de Reddit disponibles en RapidAPI:

| Proveedor | Fortaleza | Uso |
|---|---|---|
| reddit3 | Paginación estable, amplia colección | Posts (primario) |
| reddit34 | Árbol de comentarios, timestamps, sort=new | Comentarios (primario) |
| reddapi | Fallback ligero | Backup de posts y comentarios |

Ninguna de estas APIs es oficial de Reddit. Todas tienen cuotas gratuitas limitadas. La estrategia de fallback existe precisamente porque ninguna es completamente fiable por sí sola.

**El User-Agent de reddapi**

reddapi requiere `User-Agent: RapidAPI Playground` para evitar bloqueo de Cloudflare. Sin este header, la API devuelve 403. Esta es una dependencia de un detalle operativo externo y potencialmente frágil. Está documentada explícitamente en `docs/integrations/reddit/api-strategy.md`.

### DeepSeek

DeepSeek es el modelo de lenguaje que evalúa los posts. Se conecta vía el SDK de OpenAI con `base_url` personalizada. El modelo configurado por defecto es `deepseek-chat`.

La integración usa `structured output`: se le pide al modelo que devuelva un JSON que cumpla el esquema de `AIRawResponse`. Esto reduce la probabilidad de respuestas que no se puedan parsear.

### Telegram Bot API

El sistema usa la Bot API de Telegram, que es un endpoint HTTP simple. `send_message` hace un POST con el token del bot, el chat ID y el texto HTML.

Telegram soporta un subconjunto de HTML para formateo: `<b>`, `<i>`, `<a>`, `<blockquote>`. `renderer.py` usa exactamente esos tags para formatear los mensajes.

---

## 16. Tests: qué cubren y qué enseñan del diseño

### La suite actual

396 tests totales, 4 skipped (los smoke tests live que requieren credenciales reales, se saltan en CI por diseño).

Los tests se organizan en cinco categorías cualitativas:

1. **Tests unitarios por módulo**: prueban que cada función hace lo que dice
2. **Tests de integración operacional**: prueban que las fases del pipeline no interfieren entre sí
3. **Tests de smoke live**: llaman a las APIs reales para verificar que la integración funciona
4. **Tests de CI**: verifican que el workflow de GitHub Actions está correctamente configurado
5. **Tests documentales**: leen artefactos del repositorio y verifican coherencia documental

### Qué enseñan los tests de integración

Los tests de integración en `test_integration/test_operational.py` son los más instructivos para entender el diseño.

**`TestRetryWithoutAIReEvaluation`**

Verifica que un post en `pending_delivery` en el siguiente ciclo se reintenta en Telegram sin llamar a `evaluate_batch` ni a los proveedores de Reddit.

Este test no prueba solo que el código funciona. Prueba que una decisión de diseño se mantiene: la IA no re-evalúa lo que ya evaluó. Esa propiedad tiene consecuencias en el coste de API, la consistencia de las decisiones y la carga en los sistemas externos.

**`TestDeliveryBoundaryIsolation`**

Verifica que el módulo de delivery solo consume registros persistidos. Nunca re-entra en colección ni evaluación.

Este test usa un `sentinel`: una función que lanza `AssertionError` si se llama. Si el módulo de delivery intentara llamar al evaluador, el test fallaría con una excepción de `AssertionError`, no con un error de lógica de negocio. Es una técnica de verificación de fronteras arquitectónicas.

**`TestMultiRunMemoryBoundaries`**

Ejecuta el pipeline dos veces con SQLite real (no mock). Verifica que:
- Los posts marcados `sent` en la primera ejecución no entran en la segunda
- Los posts marcados `rejected` en la primera ejecución no entran en la segunda
- Los posts en `pending_delivery` después de la primera ejecución se reintenten en la segunda

Este test usa SQLite real porque la semántica del modelo de estados solo se puede verificar con persistencia real. Un mock de SQLite podría devolver lo que el test espera, pero no verificaría que el SQL real produce ese comportamiento.

### Tests documentales: una categoría inusual

`test_settings_govern_runtime.py` lee archivos del repositorio y hace aserciones de texto. Por ejemplo:

```python
def test_daily_review_limit_documents_pre_ia_cap():
    content = Path("docs/architecture.md").read_text()
    assert "antes de la evaluación IA" in content or "pre-IA" in content
```

Esto puede parecer extraño. ¿Por qué testear documentación?

La razón: hay un contrato documental entre operadores y desarrolladores sobre qué significa `daily_review_limit`. Si alguien actualiza la documentación y rompe esa semántica, el test falla. Los contratos documentales son tan rompibles como los contratos de código, pero sin tests, los primeros se rompen silenciosamente.

### `test_import_smoke.py`: detectar errores de importación

Este test importa dinámicamente todos los módulos del paquete y verifica que ninguno lanza `ImportError`, `SyntaxError` o cualquier excepción en la inicialización. Es especialmente útil para detectar errores en la inicialización de `Settings()` (que ocurre en tiempo de importación).

Si añades un módulo nuevo que importa una dependencia no instalada, este test lo detectará antes de que el problema llegue a producción.

### Cómo leer un test para entender el diseño

Cuando leas un test, hazte estas preguntas:

1. ¿Qué comportamiento específico está verificando?
2. ¿Por qué ese comportamiento importa para el sistema?
3. ¿Qué decisión de diseño refleja?
4. ¿Qué pasaría si ese comportamiento cambiara?

Los tests que responden bien a esas preguntas son especificación ejecutable. Los tests que solo verifican que `assert result == 42` sin contexto son menos informativos.

---

## 17. Decisiones de diseño y trade-offs

### 17.1 Monolito modular vs microservicios

**Decisión**: un solo proceso Python con módulos internos.

**Por qué**: el sistema ejecuta una vez al día. Los módulos no tienen requisitos distintos de escalado. La complejidad de comunicación entre servicios no compra nada aquí.

**Trade-off**:
- Ventaja: despliegue simple, sin infraestructura de mensajería, sin problemas de latencia entre servicios
- Coste: si el sistema creciera mucho (múltiples subreddits, múltiples canales, análisis histórico), el monolito empezaría a tener problemas de acoplamiento interno

**Cuándo cambiaría**: si partes distintas del sistema necesitaran escalarse independientemente o tener ciclos de deployment separados.

### 17.2 Contratos Pydantic explícitos

**Decisión**: todos los datos entre módulos pasan por modelos Pydantic en `shared/contracts.py`.

**Por qué**: las APIs de Reddit son heterogéneas. DeepSeek puede devolver estructuras inesperadas. Sin validación explícita, los errores se propagan silenciosamente.

**Trade-off**:
- Ventaja: validación temprana, documentación implícita, errores en el punto de origen no en el punto de uso
- Coste: obliga a pensar los contratos antes de implementar. Añadir un campo nuevo requiere actualizar el modelo.

### 17.3 Contenedor efímero + cron externo

**Decisión**: no tener un proceso persistente. El sistema arranca, ejecuta y termina.

**Por qué**: el caso de uso es batch diario. Un servidor 24/7 para ejecutar una vez al día añade complejidad de monitorización, reconnection y gestión de estado en memoria sin ningún beneficio.

**Cómo funciona**: un cron en el VPS host ejecuta `docker-compose up` a una hora específica. El contenedor corre el pipeline y termina. El volumen Docker mantiene la base de datos SQLite entre ejecuciones.

**Trade-off**:
- Ventaja: operaciones simples, sin gestión de procesos colgados, coste mínimo de infraestructura
- Coste: no puede reaccionar a eventos en tiempo real. No puede ejecutarse más frecuentemente que el intervalo del cron.

### 17.4 SQLite en lugar de base de datos cliente-servidor

**Decisión**: SQLite como única persistencia.

**Por qué**: el pipeline es de un solo proceso. SQLite no tiene overhead de conexión de red, no requiere proceso separado, y el archivo puede versionarse o inspeccionarse con herramientas estándar.

**Trade-off**:
- Ventaja: simplicidad brutal. Cero configuración. Cero infraestructura adicional.
- Coste: sin concurrencia de escritura. Sin consultas analíticas complejas eficientes. Sin acceso desde múltiples máquinas.

### 17.5 Comentarios solo para posts ya seleccionados

**Decisión**: no pedir comentarios en la colección inicial. Solo para los posts que ya pasaron el filtrado upstream.

**Por qué**: las llamadas a APIs de comentarios consumen cuota significativamente más rápido que las de posts. Pedir comentarios para 20+ candidatos cuando solo 8 pasarán al evaluador sería malgastar cuota en datos que nunca se usarán.

**Trade-off**:
- Ventaja: ahorro de cuota de API
- Coste: los filtros upstream (ya procesados, is_complete, recency) trabajan sin contexto de comentarios. Puede que se descarte un post que hubiera merecido revisarse si se hubieran visto sus comentarios primero.

### 17.6 Evaluación en dos fases: DECIDE → GENERA

**Decisión**: el system prompt exige que el modelo primero decida si acepta o rechaza, y solo entonces genere contenido.

**Por qué**: sin este orden, el modelo tiende a generar una respuesta plausible y luego racionalizar la aceptación. Con el orden inverso, el resultado es un sesgo hacia aceptar más de lo que debería.

**Trade-off**:
- Ventaja: mayor precisión en la decisión de aceptación
- Coste: el prompt es más largo y explícito. El sistema depende de que el modelo siga el orden indicado.

### 17.7 Weekend guard en el código, no en el cron

**Decisión**: `main.py` comprueba explícitamente si el día actual es fin de semana y hace `return` antes de ejecutar nada.

**Por qué**: si solo dependieras del cron para controlar cuándo ejecuta, un cambio de cron podría hacer que el sistema ejecutara en fin de semana sin que ninguna lógica en el código lo impidiera. La invariante de negocio ("solo días laborables") no debe delegarse completamente a infraestructura.

**Trade-off**:
- Ventaja: la lógica de negocio está en el código, es testeable y es verificable
- Coste: pequeña redundancia entre el cron y el guard interno

---

## 18. Qué enseña este proyecto sobre desarrollo con IA

### La IA no escribe el proyecto por ti

Este proyecto se construyó con asistencia de modelos de lenguaje (Claude, GPT). Pero la IA no diseñó la arquitectura, no decidió los trade-offs y no implementó los casos límite. El desarrollador hizo todo eso.

La IA fue útil para:
- debatir alternativas de diseño antes de decidir
- implementar código a partir de una especificación detallada
- escribir tests para comportamientos ya pensados
- identificar errores en código que el desarrollador presentó
- revisar consistencia entre documentación y código

No fue útil como reemplazo del criterio de ingeniería. Una IA sin criterio propio produce código que "funciona" pero no diseños que resisten el tiempo.

### SDD: especifica antes de implementar

El proceso de construcción usó Spec-Driven Development (SDD). Antes de implementar cualquier módulo había:

1. Discovery del problema
2. Proposal del change
3. Spec funcional con escenarios Given/When/Then
4. Design técnico
5. Tasks de implementación
6. Verificación post-implementación
7. Archivo

Este ciclo existe porque la IA ejecuta muy bien instrucciones precisas y muy mal instrucciones ambiguas. Cuanto más detallada la especificación, mejor el resultado. Cuanto más ambigua, más revisión necesaria.

**La lección práctica**: cuando uses IA para implementar, no pidas "implementa el módulo de evaluación". Pide "implementa la función `_evaluate_single_raw` que recibe un `ThreadContext`, llama a DeepSeek con el modelo especificado, valida la respuesta con `AIRawResponse` y devuelve `AcceptedOpportunity` o `RejectedPost`. Si la validación falla, lanza `ValidationError`. Los campos `post_id`, `title` y `link` del resultado se construyen desde el `ThreadContext`, nunca se solicitan al modelo."

La segunda instrucción produce código útil a la primera o segunda iteración. La primera produce algo que hay que reescribir.

### Los agentes necesitan contexto, no solo inteligencia

El proyecto usa herramientas de contexto persistente (Engram para memoria entre sesiones) y análisis estructural del código (GitNexus para navegar el repositorio como grafo). Estas herramientas no hacen que la IA sea más inteligente; la hacen más informada.

Sin contexto, el agente trabaja sobre lo que le cuentas en esa sesión. Con contexto, puede recuperar decisiones pasadas, entender el impacto de sus cambios y no repetir errores ya corregidos.

La lección: la calidad del output de un agente IA depende tanto del contexto que le das como de la instrucción concreta.

### Los hardening changes tienen tanto valor como los features

De los 13 changes del proyecto, cuatro (8, 9, 10, 11) no añadieron funcionalidad nueva. Cerraron la brecha entre lo que el sistema decía que hacía y lo que realmente hacía:

- el guard de fin de semana estaba documentado pero no implementado
- `review_window_days` era un setting decorativo (no llegaba al código)
- `DB_PATH` no apuntaba al volumen Docker
- no había CI automatizado

Para un junior, la tentación es medir el progreso en funcionalidades. La ingeniería madura mide también la confiabilidad: que el sistema haga lo que dice que hace.

---

## 19. Errores de lectura comunes en juniors

### Error 1: confundir carpetas con funcionalidad

Ver `delivery/`, `evaluation/`, `reddit/` y asumir que el sistema está completamente implementado sin leer el código. O al contrario: ver que hay carpetas con nombres de módulos y asumir que están vacías. El árbol de archivos es una pista, no una respuesta.

### Error 2: asumir que lo que dice la documentación es lo que hace el código

Este repo tiene documentación actualizada y coherente con el código porque hubo changes específicos dedicados a alinearlos. En proyectos reales, esa alineación no siempre existe. Siempre verifica en el código, especialmente para comportamientos críticos.

### Error 3: ignorar los tests como fuente de comprensión

Los tests son la especificación más precisa del sistema. Si quieres saber exactamente cómo funciona el selector de entrega, lee `test_selector.py`. Te dirá exactamente qué casos se cubren y cómo.

### Error 4: mezclar cuatro verdades distintas

En este proyecto hay cuatro fuentes de verdad con roles distintos:

| Fuente | Rol |
|---|---|
| `docs/product/product.md` | qué debe hacer el producto |
| `docs/architecture.md` | cómo está organizado el sistema |
| `openspec/changes/archive/` | cómo se construyó |
| `src/auto_reddit/` | qué hace hoy |

Mezclarlas lleva a confusión. Un junior que lee `TFM/diario.md` y toma las decisiones del día 1 como vigentes está leyendo historia como si fuera presente.

### Error 5: ignorar los enums como decisiones de diseño

Ver `OpportunityType` con cuatro valores y pensar "ah, es una lista de strings". Los enums cerrados son contratos que limitan intencionalmente el espacio de valores posibles. Si el negocio necesita un quinto tipo, requiere una decisión explícita de añadirlo al enum, no simplemente añadir un string libre.

### Error 6: no distinguir errores transitorios de permanentes

Ver `except Exception: return None` y pensar que el sistema silenacia errores. La distinción entre errores que se reintenten y errores que se saltan es una decisión de diseño con consecuencias en la consistencia del estado. Lee el manejo de excepciones despacio.

### Error 7: subestimar la complejidad del fallback chain

Ver `reddit3 → reddit34 → reddapi` y pensar "ah, tres APIs de backup". La estrategia es más sutil: el orden difiere entre posts y comentarios, la calidad varía por proveedor, y esa calidad afecta el comportamiento del evaluador IA downstream. Todo el `ContextQuality` enum existe precisamente para comunicar esa variación.

### Error 8: creer que `main.py` es el mejor punto de entrada para entender el sistema

`main.py` es el mejor punto de entrada para entender el flujo. Pero para entender el sistema, el mejor punto de entrada es `shared/contracts.py`. Los contratos te dicen qué existe y cómo está representado antes de entender cómo se crea o se transforma.

---

## 20. Evolución histórica del proyecto

> **Nota**: esta sección es histórica. Describe cómo se construyó el proyecto, no cómo funciona hoy. Para entender el estado actual, lee las secciones anteriores.

### Origen y motivación

El proyecto surgió de una experiencia en una empresa que trabaja con Odoo. La observación inicial: el equipo de marketing perdía conversaciones relevantes en Reddit porque monitorizarlo a mano era irregular y costoso.

La primera definición del sistema fue mucho más amplia que la versión actual: incluía publicación automática, análisis de múltiples subreddits y un backlog editorial. A lo largo del proceso de discovery, el alcance se redujo deliberadamente hasta un sistema que detecta y prepara, nunca publica.

### La evolución del modelo de estados de persistencia

La primera versión del modelo de estados incluía `approved` como estado intermedio entre la evaluación IA y la entrega Telegram. El problema: `approved` no añadía valor real porque cualquier cosa que la IA aceptaba pasaba directamente a entrega. Era un estado administrativo sin consecuencias en el flujo.

`approved` fue eliminado, y el modelo quedó en tres estados: `pending_delivery` (IA aceptó, entrega pendiente), `sent` (entregado), `rejected` (rechazado).

Esta simplificación es un ejemplo de diseño hacia adelante: cuando un estado no tiene consecuencias distintas de las de otro estado, elimínalo.

### Los 13 changes en cuatro fases

**Fase 1 — pipeline principal (changes 1-5, 27-28/03/2026)**

1. `reddit-candidate-collection`: colección de posts con fallback chain
2. `candidate-memory-and-uniqueness`: SQLite, modelo de estados, idempotencia
3. `thread-context-extraction`: comentarios con fallback chain y ContextQuality
4. `ai-opportunity-evaluation`: evaluador DeepSeek con prompt de dos fases
5. `telegram-daily-delivery`: selector, renderer, cliente Telegram, deliver_daily

**Fase 2 — integración, smoke y hardening (changes 6-10, 28-29/03/2026)**

6. `operational-integration-tests`: tests de integración entre fases del pipeline
7. `telegram-smoke-tests`: smoke tests live contra la Bot API real
8. `runtime-documented-truth-alignment`: cerrar cuatro derives entre documentación y runtime
9. `environment-persistence-execution-hardening`: contrato de despliegue Docker cerrado
10. `minimum-ci-baseline`: GitHub Actions automatizando la suite en cada push y PR

**Fase 3 — alineación semántica (change 11, 30/03/2026)**

11. `settings-govern-runtime`: documentar la semántica de settings con distinción pre-IA/post-IA

**Fase 4 — limpieza de artefactos históricos (changes 12-13, 30/03/2026)**

12. `connect-or-remove-half-landed-logic`: eliminar marcadores `# Change N` del código activo
13. `docs-information-architecture-cleanup`: reorganizar la arquitectura de información documental

### Por qué los changes 8-13 son tan valiosos pedagógicamente

Los cambios de funcionalidad (1-5) son los que un junior suele considerar "el trabajo real". Los changes de hardening y alineación (6-13) son los que distinguen un sistema que funciona de un sistema en el que se puede confiar.

Change 8 cerró cuatro derives entre documentación y comportamiento real. Change 9 cerró un bug silencioso de despliegue que no producía error pero perdía datos. Change 10 añadió la red de seguridad que detecta regresiones automáticamente. Change 11 documentó semántica que hasta entonces era implícita.

Ninguno de esos cambios añadió funcionalidad nueva. Todos hacen el sistema más confiable, predecible y mantenible.

---

## 21. Glosario técnico

**adaptador**: módulo cuya responsabilidad es absorber la heterogeneidad de una fuente externa y entregar un contrato homogéneo al resto del sistema. `reddit/client.py` y `reddit/comments.py` son adaptadores.

**blast radius**: conjunto de símbolos y módulos que se ven afectados cuando cambias uno concreto. Antes de tocar un contrato compartido, conviene medir el blast radius.

**boundary isolation test**: test que verifica que una fase del pipeline no llama a otra fase que no le corresponde. Usa una función sentinel que lanza `AssertionError` si se invoca.

**cap**: límite configurable. `daily_review_limit` es el cap pre-evaluación IA; `max_daily_opportunities` es el cap post-evaluación IA.

**CI baseline**: primer nivel de integración continua automatizada. En este proyecto es el workflow de GitHub Actions que ejecuta la suite en cada push y PR a `main`.

**computed field**: campo de un modelo Pydantic que se calcula automáticamente a partir de otros campos. `is_complete` en `RedditCandidate` es un computed field.

**conftest.py**: archivo especial de pytest que configura el entorno antes de la colección de tests. En este proyecto establece defaults dummy para las variables de entorno obligatorias, permitiendo que los tests corran en CI sin `.env`.

**contrato**: estructura de datos compartida entre módulos. En este repo los contratos son los modelos Pydantic de `shared/contracts.py`.

**ContextQuality**: enum que indica la riqueza del contexto de hilo extraído según el proveedor. `full` (reddit34), `partial` (reddit3), `degraded` (reddapi).

**cursor**: token opaco que una API devuelve para indicar el punto de inicio de la siguiente página. Cada proveedor de Reddit usa un campo diferente.

**decisión final**: estado en el modelo de persistencia que no puede revertirse. `sent` y `rejected` son decisiones finales en este sistema.

**dos fases en el prompt**: patrón de diseño de prompts donde el modelo primero DECIDE (acepta/rechaza) y luego GENERA contenido. Evita que la IA escriba una respuesta plausible y luego racionalice la aceptación.

**efímero**: que existe temporalmente y termina. El contenedor Docker de este sistema es efímero: arranca, ejecuta y termina.

**enum cerrado**: enumeración con valores fijos definidos en código. Si la IA devuelve un valor que no está en el enum, Pydantic lanza `ValidationError`.

**env-gated test**: test que se salta automáticamente si no existe una variable de entorno específica. Útil para smoke tests que no deben ejecutarse en CI.

**extra="ignore"**: configuración de pydantic-settings que permite variables adicionales en `.env` sin que `Settings` falle. Necesario porque `.env` puede contener variables de smoke que `Settings` no declara.

**fallback chain**: cadena ordenada de proveedores. Si el primero falla, se intenta el siguiente. Posts: `reddit3 → reddit34 → reddapi`. Comentarios: `reddit34 → reddit3 → reddapi`.

**gap silencioso**: error de configuración que no produce error ni advertencia pero altera el comportamiento. `DB_PATH` apuntando a la capa efímera del contenedor es el ejemplo canónico.

**idempotencia**: propiedad de una operación que produce el mismo resultado si se ejecuta varias veces. Los upserts de SQLite en este sistema son idempotentes.

**is_complete**: computed field de `RedditCandidate`. `True` solo si todos los campos mínimos del contrato están presentes y no son `None`. El contrato mínimo incluye `post_id`, `title`, `url`, `permalink`, `subreddit`, `created_utc` (distinto de cero), `source_api`, y además que `selftext` y `author` no sean `None`. `num_comments` no forma parte del contrato mínimo y no afecta a `is_complete`.

**knob decorativo**: setting que existe en `Settings` y en `.env.example` pero cuyo valor no llega a gobernar el runtime porque el código usa una constante hardcodeada en lugar de leerlo. `review_window_days` era un knob decorativo antes del change 8.

**monolito modular**: una sola aplicación con módulos internos bien separados. Sin microservicios.

**normalizer**: función que transforma la respuesta heterogénea de una API externa al contrato propio del sistema.

**pending_delivery**: estado transitorio en el modelo de persistencia. Significa que la IA aceptó el post pero Telegram aún no confirmó la entrega.

**prompt cacheado**: system prompt estático que los modelos modernos pueden mantener en caché de prefijo para reducir latencia y coste.

**purge_expired**: método de `CandidateStore` que elimina registros `pending_delivery` con TTL expirado al final del ciclo de entrega.

**retry-first selection**: política de priorización en el selector de entregas. Los registros con intentos fallidos de entrega previos se seleccionan antes que los nuevos dentro del cap diario.

**runtime governance**: alineación entre los settings declarados y el comportamiento observable del sistema. Un setting que gobierna de verdad el runtime cambia el comportamiento cuando se cambia su valor.

**SDD (Spec-Driven Development)**: metodología de desarrollo donde la especificación precede a la implementación. Ciclo: discovery → proposal → spec → design → tasks → apply → verify → archive.

**sent solo tras confirmación**: el estado `sent` no se escribe en SQLite hasta que Telegram confirma la entrega. Un fallo de red no produce un post marcado como enviado sin haberlo entregado.

**split truth**: situación en que dos settings distintos controlan el mismo concepto con el mismo valor por defecto. Es una trampa de mantenimiento: actualizar uno y olvidar el otro produce comportamiento divergente silencioso.

**structured output**: respuesta de un modelo de lenguaje forzada a cumplir un esquema JSON. En este proyecto DeepSeek devuelve un JSON validado por `AIRawResponse`.

**TTL (time to live)**: tiempo de vida de un registro. En este sistema, los registros `pending_delivery` tienen TTL semanal que varía según el día de la semana en que se tomó la decisión.

**upsert**: operación de base de datos que inserta si no existe o actualiza si ya existe. Evita duplicados sin necesidad de consultar antes de escribir.

**weekend guard**: lógica en `main.py` que comprueba si el día actual es fin de semana y hace `return` antes de ejecutar nada. Está en el código, no solo en el cron.

---

## 22. Changelog editorial de esta guía

### Qué se cambió en esta reescritura

**Contradicciones resueltas**

- Los módulos `evaluator.py`, `telegram.py`, `renderer.py`, `selector.py` y `delivery/__init__.py` estaban descritos como placeholders en la versión anterior. En la nueva versión se describen como lo que son: módulos completamente implementados.

- Los settings defaults aparecían como `max_daily_opportunities = 10` y `daily_review_limit = 10` en algunas secciones. El valor actual es 8 en ambos casos, alineado con el análisis de cuota documentado en `docs/integrations/reddit/api-strategy.md`.

- El conteo de tests era inconsistente a lo largo del documento (270, 273, 295, 339, 395, 396 aparecían en distintas secciones). El conteo actual es 396 (4 skipped).

- La sección de flujos decía "como el código del producto aún no está implementado". El pipeline completo está implementado y archivado en los 13 changes. Esa afirmación era un artefacto del momento en que se escribió esa sección.

**Estructura reorganizada**

- Se eliminó la mezcla entre estado actual e histórico en las mismas secciones. La historia va en la sección 20, claramente marcada.

- Se eliminaron las referencias a módulos como "placeholders" y se reemplazaron por descripciones del código actual.

- Las secciones de "zonas pendientes" que decían "RESUELTA" se consolidaron en la sección histórica o se eliminaron.

- La sección de OpenSpec, SDD, skills, GitNexus, Engram y MCP (sección 9 en la versión anterior) se condensó y se movió a su lugar apropiado en sección 18 (desarrollo con IA) y sección 7 (estructura del repositorio), en lugar de ocupar una sección de primer nivel desproporcionada.

**Contenido eliminado**

- El historial detallado de todos los changes (sección 16 de la versión anterior) se condensó significativamente. Los artefactos completos de cada change están en `openspec/changes/archive/`.

- Las referencias al tooling personal del autor (qué modelos usa para qué fases) se eliminaron del cuerpo principal. No aportan valor didáctico al lector; son contexto del autor, no del sistema.

- Los bloques de código que mostraban versiones intermedias del `main.py` con comentarios `# Change N (pendiente)` se eliminaron. Eran capturas históricas, no código actual.

**Contenido añadido**

- Sección de ruta recomendada de lectura del código.
- Explicación en profundidad de cada módulo con patrones de diseño concretos.
- Sección de manejo de errores transitorios vs permanentes.
- Sección de integraciones externas con análisis de por qué se usa cada API.
- Sección de errores de lectura comunes en juniors, basada en las trampas reales que tiene el repo.
- Glosario técnico reorganizado por orden alfabético.

**Contenido marcado explícitamente como histórico**

- La sección de evolución del proyecto está en sección 20, con aviso explícito al inicio.
- Las referencias a versiones intermedias del código se han movido a la sección histórica.

### Pendientes de verificación manual

El sistema prompt completo de `evaluator.py` (~280 líneas) no se transcribió en esta guía. Si el sistema prompt tiene cambios relevantes para el comportamiento del evaluador, conviene revisar `src/auto_reddit/evaluation/evaluator.py` directamente y actualizar la descripción de la sección 10.

Los snapshots JSON en `docs/integrations/reddit/*/raw/` no se leyeron para esta guía. Si se han actualizado, las descripciones de las estructuras de respuesta de cada proveedor en la sección 10 deberían verificarse.

---

## 23. Despliegue en servidor Ubuntu propio

*Añadida el 03/04/2026. Documenta el primer despliegue real del sistema en producción.*

### Contexto

El despliegue se realizó en un servidor Ubuntu 24.04 propio (no un proveedor cloud), con acceso SSH directo. La ruta elegida fue `/opt/auto-reddit`, convención estándar para aplicaciones de sistema en Linux.

### Proceso completo

**1. Clonar el repositorio**

El puerto 22 (SSH hacia GitHub) estaba bloqueado en el servidor. Se usó HTTPS:

```bash
cd /opt
sudo git clone https://github.com/Prodelaya/auto-reddit.git
cd auto-reddit
```

**2. Instalar Docker**

El servidor no tenía Docker instalado. Se instaló con apt:

```bash
sudo apt install -y docker.io docker-compose-v2
```

Versiones resultantes: Docker 28.2.2, Docker Compose 2.37.1.

**3. Configurar variables de entorno**

```bash
sudo cp .env.example .env
sudo nano .env
# Rellenar: DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, REDDIT_API_KEY
```

**4. Primera ejecución**

```bash
sudo docker compose up --build
```

Resultado: imagen construida, pipeline ejecutado, 45 candidatos recolectados, 6 aceptados por la IA, 6 mensajes entregados a Telegram, `exited with code 0`.

**5. Cron para ejecución diaria**

```bash
sudo crontab -e
```

Línea añadida:

```
30 10 * * * cd /opt/auto-reddit && docker compose up >> /var/log/auto-reddit.log 2>&1
```

El pipeline se ejecuta cada día a las 10:30 hora del servidor. El guard de fin de semana está en `main.py`, no en el cron.

### Cosas que aprender de este despliegue

**El puerto 22 puede estar bloqueado.** En servidores propios o corporativos es habitual que el firewall bloquee el puerto SSH saliente hacia GitHub. HTTPS es la alternativa directa; no requiere configuración adicional para repos públicos.

**Los 429 son normales, no son errores del despliegue.** Los proveedores de la API de Reddit tienen rate limits estrictos. El sistema tiene lógica de fallback entre tres proveedores (`reddit34` → `reddit3` → `reddapi`). Ver los 429 en los logs no significa que el despliegue haya fallado; significa que el sistema está funcionando como se diseñó.

**El log no se crea hasta la primera ejecución del cron.** Si se lanza el pipeline manualmente con `docker compose up`, los logs van a la terminal, no al fichero `/var/log/auto-reddit.log`. Ese fichero lo crea el cron la primera vez que se ejecuta.

**El volumen Docker persiste entre ejecuciones.** La base de datos SQLite vive en `auto-reddit_sqlite_data`. Los posts ya entregados no se reenvían aunque el contenedor muera y se vuelva a levantar. Esto es una decisión de diseño deliberada, no un efecto secundario.

### Referencia

La guía operativa completa con todos los comandos exactos está en [`docs/deployment.md`](../docs/deployment.md).
