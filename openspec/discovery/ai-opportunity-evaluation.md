# Product Discovery Brief: ai-opportunity-evaluation

## Classification
- Confirmado: El trabajo se clasifica como `single-change` porque resuelve un unico resultado funcional coherente: evaluar con IA los posts ya seleccionados y enriquecidos aguas arriba, decidir si representan una oportunidad valida y producir salida estructurada para revision humana.
- Inferido: Mantener este cambio aislado evita mezclar evaluacion IA con extraccion de contexto, delivery por Telegram, persistencia de estados finales o backlog editorial.
- Pendiente: Ninguno.

## Problem Statement
- Confirmado: El flujo necesita decidir para cada post enriquecido si representa una oportunidad valida de participacion en Reddit, clasificar el tipo de rechazo cuando no lo es y generar la informacion estructurada que el equipo humano necesita para decidir si intervenir.
- Confirmado: Sin este cambio, el pipeline tiene contexto de hilo normalizado pero no tiene forma de filtrar posts resueltos/cerrados/no aptos ni de producir la salida que alimenta el delivery posterior.
- Inferido: La IA es no deterministica; el cambio debe minimizar alucinaciones y falsa confianza, delegando la decision final de envio al humano.

## Goal / Desired Outcome
- Confirmado: Evaluar cada post con contexto de hilo (`ThreadContext`) y devolver un resultado estructurado que indique si el post es una oportunidad valida o un rechazo, con clasificacion del tipo de rechazo cuando corresponda.
- Confirmado: Para oportunidades aceptadas, producir la informacion estructurada necesaria para que el paso de delivery construya un mensaje de Telegram de forma deterministica, sin generar directamente el mensaje final.
- Confirmado: La salida estructurada para posts aceptados debe incluir: titulo, link, idioma del post, tipo de oportunidad (taxonomia cerrada), resumen del post en espanol, resumen de comentarios en espanol, respuesta sugerida en espanol y respuesta sugerida equivalente en ingles.
- Confirmado: Para posts rechazados, clasificar el tipo de rechazo en la salida estructurada.
- Confirmado: El resultado se persiste en `opportunity_data` del estado `pending_delivery` para permitir reintentos de Telegram sin reevaluacion IA.
- Inferido: El valor de este change es desacoplar la evaluacion IA del delivery, produciendo un contrato estructurado intermedio que permite retry idempotente y rendering deterministico aguas abajo.

## Primary Actor(s)
- Confirmado: Proceso diario interno de `auto-reddit`.
- Inferido: El consumidor inmediato del output es el modulo de delivery (Telegram), que construye el mensaje final a partir de la salida estructurada. El equipo humano es el consumidor ultimo del contenido.

## Stakeholders
- Equipo de marketing y contenido, que recibe las oportunidades evaluadas en Telegram y decide si intervenir.
- Responsable de producto, que fija los limites de confianza de la IA, la taxonomia de rechazos y la regla de prudencia.

## Trigger
- Confirmado: El change se ejecuta despues de que change 3 (`thread-context-extraction`) entregue los `ThreadContext` normalizados aguas arriba.
- Confirmado: Solo se evaluan los posts que llegan con contexto de hilo; los posts descartados por fallo total de contexto en change 3 no llegan aqui.

## Main Flow
1. El proceso recibe los `ThreadContext` normalizados del change 3.
2. Para cada `ThreadContext`, invoca a DeepSeek con el contexto del post y sus comentarios.
3. La IA evalua segun las reglas de elegibilidad, cierre/resolucion y estilo definidas en `docs/product/product.md` y `docs/product/ai-style.md`.
4. Si la IA acepta: produce la salida estructurada con los campos requeridos para delivery posterior.
5. Si la IA rechaza: clasifica el tipo de rechazo en la salida estructurada.
6. El resultado se persiste via el mecanismo de memoria operativa: posts aceptados como `pending_delivery` con `opportunity_data` = salida estructurada; posts rechazados como `rejected`.

## Alternative Flows / Edge Cases
- Confirmado: Si la calidad del contexto es `partial`, la IA puede evaluar normalmente; la calidad queda visible en el `ThreadContext` pero no impide la evaluacion.
- Confirmado: Si la calidad del contexto es `degraded`, la IA puede evaluar pero con prudencia reforzada: la salida debe incluir una senal de advertencia y bullet points sobre los aspectos que el humano debe revisar antes de decidir.
- Confirmado: Si la IA no puede determinar con confianza suficiente si hay oportunidad (por ejemplo, contexto insuficiente para aseverar cierre del hilo), el comportamiento correcto es abstenerse de sugerir respuesta, no inventar certeza.
- Inferido: La abstencion por falta de evidencia no es un tipo de salida separado; es una evaluacion que rechaza la oportunidad con la clasificacion de rechazo correspondiente.
- Confirmado: Si la llamada a DeepSeek falla por error transitorio (rate limit, timeout), el cambio debe reintentar. Si falla por error permanente (auth, bad request), debe fallar explicitamente.
- Pendiente: Definir si un fallo persistente de la API de DeepSeek para un post descarta ese post del batch del dia o detiene el pipeline completo.

## Business Rules
- Confirmado: El change se clasifica como `single-change`.
- Confirmado: La evaluacion se hace sobre `ThreadContext` ya normalizado; no recupera posts ni comentarios por si mismo.
- Confirmado: La taxonomia de tipos de oportunidad es una lista cerrada: funcionalidad y configuracion de Odoo, desarrollo, dudas sobre si merece la pena Odoo, comparativas con otras opciones.
- Confirmado: Los resumenes operativos (post y comentarios) se entregan en espanol para el equipo interno.
- Confirmado: La respuesta sugerida se genera en dos versiones: espanol e ingles.
- Confirmado: La publicacion final y la adaptacion de la respuesta al hilo siguen siendo decision humana; la IA no publica ni decide enviar.
- Confirmado: No existe campo de salida explicito tipo `insufficient_evidence` o `no confiar`; la evaluacion se alinea a la evidencia disponible y el humano decide si enviar.
- Confirmado: Los tipos de rechazo SI se distinguen en la salida estructurada.
- Confirmado: La salida estructurada para posts aceptados es suficiente para construir el mensaje de Telegram de forma deterministica, pero NO es el mensaje final ni un objeto gigante sin control (opcion B: resumen + estructura/sugerencias).
- Confirmado: El resultado se persiste como JSON serializado en `opportunity_data` del registro `pending_delivery`, permitiendo que el delivery reconstruya el mensaje sin reevaluar la IA.
- Confirmado: No existe estado `approved`, backlog editorial ni persistencia de `not selected today`.
- Confirmado: Las reglas de comportamiento, tono y criterios de intervencion se documentan en `docs/product/ai-style.md` y `docs/product/product.md`; este change las aplica pero no las redefine.
- Inferido: La prudencia reforzada para contexto `degraded` no impide la respuesta; implica que la salida debe senalar al humano los puntos debiles del contexto para su revision antes de enviar.

## Permissions / Visibility
- Confirmado: Uso interno del pipeline; no introduce interfaz humana de backlog ni acciones manuales sobre estados.
- Confirmado: La visibilidad externa es unicamente a traves de Telegram cuando el delivery tiene exito; este change no genera salida directa a Telegram.
- Inferido: El equipo humano interactua con el resultado solo cuando lo recibe por Telegram; no hay panel, cola ni interfaz adicional.

## Scope In
- Confirmado: Evaluacion de cada `ThreadContext` con IA (DeepSeek) segun reglas de elegibilidad y cierre/resolucion.
- Confirmado: Produccion de salida estructurada para posts aceptados: titulo, link, idioma, tipo de oportunidad, resumen del post (espanol), resumen de comentarios (espanol), respuesta sugerida (espanol + ingles).
- Confirmado: Clasificacion del tipo de rechazo en la salida estructurada para posts no aptos.
- Confirmado: Manejo de calidad de contexto: `partial` permite evaluacion normal; `degraded` permite evaluacion con prudencia reforzada + advertencia + bullets de revision humana.
- Confirmado: Persistencia del resultado: aceptados como `pending_delivery` con `opportunity_data` (salida estructurada serializada); rechazados como `rejected`.
- Confirmado: Retry de errores transitorios de la API de DeepSeek.
- Confirmado: Fallo explicito en errores permanentes de la API.

## Scope Out
- Confirmado: Recoleccion inicial de candidatos desde Reddit.
- Confirmado: Extraccion y normalizacion de contexto de hilo (change 3).
- Confirmado: Memoria operativa de exclusion por decisiones finales (change 2).
- Confirmado: Entrega por Telegram, formateo de mensajes, reintentos de delivery.
- Confirmado: Publicacion en Reddit o cualquier decision de envio autonoma.
- Confirmado: Backlog editorial, cola manual, estado `approved` o persistencia de `not selected today`.
- Confirmado: Redefinir las reglas de estilo y comportamiento de la IA (viven en `ai-style.md`, no en este change).

## Acceptance Criteria
- [ ] El change evalua unicamente `ThreadContext` recibidos aguas arriba; no recupera posts ni comentarios.
- [ ] Para posts aceptados, la salida estructurada incluye: titulo, link, idioma, tipo de oportunidad (lista cerrada), resumen del post en espanol, resumen de comentarios en espanol, respuesta sugerida en espanol, respuesta sugerida equivalente en ingles.
- [ ] Para posts rechazados, la salida clasifica el tipo de rechazo.
- [ ] Contexto `partial` permite evaluacion normal sin impedimento.
- [ ] Contexto `degraded` permite evaluacion pero la salida incluye senal de advertencia y bullet points sobre lo que el humano debe revisar antes de decidir.
- [ ] No existe campo de salida explicito tipo `insufficient_evidence`; la evaluacion se alinea a la evidencia disponible.
- [ ] La salida estructurada para aceptados es suficiente para rendering deterministico posterior, no es un mensaje de Telegram preformateado ni un objeto sin control.
- [ ] El resultado se persiste: aceptados como `pending_delivery` con `opportunity_data` = salida estructurada JSON; rechazados como `rejected`.
- [ ] Un retry de Telegram tras aceptacion IA reutiliza `opportunity_data` sin reevaluar la IA.
- [ ] Errores transitorios de DeepSeek se reintentan; errores permanentes fallan explicitamente.
- [ ] No se introduce estado `approved`, backlog editorial ni persistencia de `not selected today`.

## Non-Functional Notes
- Confirmado: El modelo recomendado es `deepseek-chat` (DeepSeek-V3) en modo non-thinking, consumido via SDK de OpenAI apuntando a `https://api.deepseek.com`.
- Confirmado: Structured output via `response_format` JSON del SDK, parseable directamente por modelos Pydantic.
- Confirmado: La API key se carga desde `config/settings.py` via pydantic-settings; nunca se hardcodea.
- Confirmado: El system prompt debe alinearse con las reglas de `ai-style.md` y `product.md`.
- Inferido: El volumen maximo es 8 evaluaciones por dia; la presion de cuota de DeepSeek es marginal en este volumen con cache hit del system prompt.
- Inferido: El prompt debe instruir a la IA a no sobreafirmar, no inventar informacion y ser prudente en temas tecnicos complejos, segun los principios de `ai-style.md`.

## Assumptions
- Confirmado: Changes 1, 2 y 3 ya cerraron que la coleccion inicial no incluye comentarios, que el recorte diario a 8 ocurre antes de la evaluacion y que el contexto de hilo se normaliza a `ThreadContext` con indicador de calidad.
- Confirmado: `docs/product/ai-style.md` y `docs/product/product.md` son las fuentes de verdad para las reglas de comportamiento, tono, criterios de intervencion y taxonomia de tipos de oportunidad.
- Confirmado: El contrato de `ThreadContext` (`shared/contracts.py`) ya esta definido con `candidate`, `comments`, `comment_count`, `quality`, `source_api`.
- Confirmado: El mecanismo de persistencia (`CandidateStore`) ya soporta `save_pending_delivery(post_id, opportunity_data_json)` y `save_rejected(post_id)`.
- Inferido: El prompt engineering concreto, las instrucciones exactas al modelo y la validacion estricta del JSON de salida se definiran en SDD; la discovery establece el contrato funcional sin entrar en diseno tecnico del prompt.

## Open Decisions
- Pendiente: Definir en SDD si un fallo persistente de DeepSeek para un post descarta ese post del batch del dia o detiene el pipeline completo. La discovery no bloquea por esto porque el outcome funcional (evaluar y clasificar) ya esta confirmado.
- Pendiente: Definir en SDD la forma exacta de serializar la salida estructurada en `opportunity_data` (schema Pydantic concreto), respetando que sea suficiente para rendering deterministico pero no un objeto gigante ni un mensaje Telegram preformateado.
- Pendiente: Definir en SDD los tipos concretos de rechazo que la IA puede clasificar, alineados con las reglas de cierre/resolucion de `product.md` seccion 8 y los criterios de no intervencion de `ai-style.md` seccion 5.
- Pendiente: Definir en SDD la forma exacta de la senal de advertencia y los bullet points de revision humana para contexto `degraded`.

## Risks
- Confirmado: Si la IA sobreafirma con contexto insuficiente, el equipo humano recibira una oportunidad falsa. La mitigacion esta en las reglas de prudencia de `ai-style.md` y en que el humano decide si enviar.
- Confirmado: Si el prompt no instruye adecuadamente sobre contexto `degraded`, la IA podria tratar contexto parcial como completo sin senalar la debilidad. La mitigacion es la regla de prudencia reforzada + advertencia + bullets.
- Confirmado: Si la salida estructurada de `opportunity_data` incluye el mensaje Telegram preformateado en vez de la estructura para rendering posterior, se pierde flexibilidad de delivery y se mezclan responsabilidades. La regla de opcion B (resumen + estructura) lo previene.
- Confirmado: Si se introduce un campo explicito de `insufficient_evidence`, se crea una cuarta categoria de salida que rompe el contrato binario (aceptado/rechazado) y complica la logica de persistencia y delivery. La decision de no incluirlo lo previene.
- Inferido: La no-determinismo de la IA significa que la misma entrada podria producir resultados diferentes en distintas ejecuciones. Esto no es un riesgo de este change sino una caracteristica inherente; la mitigacion es que el humano decide siempre.

## Readiness for SDD
Status: ready-for-sdd
Reason: El problema, objetivo, actor, trigger, flujo principal, reglas de negocio, limites de alcance y criterios de aceptacion estan suficientemente cerrados. Los puntos abiertos pendientes son detalles de implementacion tecnica (schema Pydantic concreto, tipos de rechazo exactos, forma de la advertencia para degraded, comportamiento ante fallo persistente de API) que se definen naturalmente en SDD sin cambiar el outcome funcional: evaluar posts con contexto normalizado, clasificar aceptacion/rechazo, producir salida estructurada para rendering deterministico posterior y persistir para retry sin reevaluacion.
