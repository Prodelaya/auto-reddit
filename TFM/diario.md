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
