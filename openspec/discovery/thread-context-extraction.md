# Product Discovery Brief: thread-context-extraction

## Classification
- Confirmado: El trabajo se clasifica como `single-change` porque resuelve un unico resultado funcional coherente: enriquecer solo los posts ya seleccionados aguas arriba con `contexto bruto normalizado` del hilo.
- Inferido: Mantener este cambio aislado evita mezclar extraccion de contexto con decisiones editoriales, evaluacion IA o delivery.
- Pendiente: Ninguno.

## Problem Statement
- Confirmado: El flujo necesita recuperar contexto adicional del hilo solo para los posts ya seleccionados aguas arriba, porque la coleccion inicial no trae comentarios y la evaluacion posterior requiere mas contexto que el post base.
- Inferido: Sin este cambio, la evaluacion posterior tendria que decidir con contexto insuficiente o acoplar directamente la lectura de APIs de Reddit dentro del modulo de IA.
- Pendiente: Ninguno.

## Goal / Desired Outcome
- Confirmado: Entregar para cada post seleccionado un `contexto bruto normalizado` del hilo, listo para consumo aguas abajo, sin resumirlo ni convertirlo aun en juicio editorial o salida de IA.
- Confirmado: El contrato debe incluir un indicador simple de degradacion de contexto para reflejar si la extraccion uso una fuente degradada o llego incompleta.
- Inferido: El valor de este change es desacoplar la obtencion y normalizacion del contexto respecto del analisis posterior.
- Pendiente: Ninguno.

## Primary Actor(s)
- Confirmado: Proceso diario interno de `auto-reddit`.
- Inferido: El consumidor inmediato es el change 4 (`ai-opportunity-evaluation`), no el equipo humano final ni Telegram directamente.
- Pendiente: Ninguno.

## Stakeholders
- Equipo de marketing y contenido, que recibira despues solo oportunidades ya evaluadas.
- Responsable de producto, que fija el limite entre extraccion de datos y juicio editorial.

## Trigger
- Confirmado: El change se ejecuta despues de que change 2 entregue los posts elegibles ya recortados aguas arriba.
- Inferido: Solo corre para posts que siguen vivos en el batch diario tras coleccion y memoria operativa.
- Pendiente: Ninguno.

## Main Flow
1. El proceso recibe posts ya seleccionados aguas arriba para revision posterior.
2. Recupera por post el contenido y comentarios disponibles del hilo usando la estrategia operativa vigente de APIs y fallbacks.
3. Normaliza el material recuperado a un contrato comun de contexto bruto del hilo.
4. Marca de forma simple si el contexto llega completo o degradado.
5. Entrega ese contexto bruto normalizado al siguiente paso aguas abajo.

## Alternative Flows / Edge Cases
- Confirmado: Si una fuente de comentarios/contexto falla, el proceso puede degradar a otra fuente segun la estrategia vigente de fallback.
- Confirmado: Si todas las APIs de comentarios/contexto fallan para un post ya seleccionado, ese post se descarta del batch del dia.
- Confirmado: `reddapi` puede aportar contexto degradado de comentarios, pero no equivale a comentarios recientes reproducibles ni a un arbol completo comparable con `reddit34`.
- Inferido: La degradacion debe ser visible en el contrato para que aguas abajo sepa si evalua con contexto parcial.
- Pendiente: La profundidad/cobertura exacta que debe esperarse del raw real de cada provider debe revisarse y recomendarse en una fase SDD posterior; no se cierra aqui como requisito funcional nuevo.

## Business Rules
- Confirmado: El change se clasifica como `single-change`.
- Confirmado: Solo se recupera contexto para posts ya seleccionados aguas arriba; no se consultan comentarios en la coleccion inicial.
- Confirmado: La salida de este change es `contexto bruto normalizado`, no un resumen para IA ni una oportunidad ya evaluada.
- Confirmado: Este change NO decide si un hilo esta resuelto, cerrado o si merece respuesta; eso pertenece a change 4 y a las reglas de IA en `docs/product/ai-style.md`.
- Confirmado: Si todas las APIs de contexto fallan para un post seleccionado, ese post queda fuera del batch del dia.
- Confirmado: El contrato debe exponer un indicador simple de degradacion de contexto.
- Inferido: La degradacion expresa calidad/cobertura de la extraccion, no una decision de negocio.
- Pendiente: Ninguno.

## Permissions / Visibility
- Confirmado: Uso interno del pipeline; no introduce interfaz humana ni salida directa a Telegram.
- Inferido: La visibilidad externa sigue siendo nula en este change porque todavia no hay evaluacion ni delivery.
- Pendiente: Ninguno.

## Scope In
- Confirmado: Recuperacion del post y sus comentarios/contexto solo para posts ya seleccionados aguas arriba.
- Confirmado: Normalizacion del contexto recuperado a un contrato interno comun.
- Confirmado: Exposicion de un indicador simple de degradacion del contexto.
- Confirmado: Descarte del post del batch cuando falle toda la cadena de APIs de contexto.

## Scope Out
- Confirmado: Recoleccion inicial de candidatos desde `r/Odoo`.
- Confirmado: Aplicacion del corte diario a 8 posts.
- Confirmado: Decidir si el hilo esta resuelto, cerrado o merece respuesta.
- Confirmado: Resumir el hilo para IA, clasificar oportunidad o generar respuesta sugerida.
- Confirmado: Entrega por Telegram o cualquier decision de publicacion.
- Confirmado: Fijar en discovery una profundidad exacta de comentarios/replies no confirmada por la documentacion vigente.

## Acceptance Criteria
- [ ] El change solo intenta recuperar contexto para posts ya seleccionados aguas arriba.
- [ ] La salida por post es `contexto bruto normalizado` del hilo, no un resumen ni una decision de oportunidad.
- [ ] El contrato expone un indicador simple de degradacion de contexto.
- [ ] Si una fuente principal falla, el change puede usar fallbacks documentados sin cambiar el limite funcional del change.
- [ ] Si todas las APIs de contexto fallan para un post seleccionado, ese post se descarta del batch del dia.
- [ ] El change no decide si el hilo esta resuelto/cerrado ni si merece respuesta.

## Non-Functional Notes
- Confirmado: La presion de cuota se concentra en comentarios por post, por lo que este change debe mantenerse aguas abajo del recorte a 8.
- Confirmado: La estrategia operativa vigente prioriza `reddit34` para comentarios por post, usa `reddit3` como fallback util y deja `reddapi` como fallback degradado.
- Inferido: La normalizacion debe tolerar diferencias de shape y metadata entre providers sin inventar campos no garantizados.
- Pendiente: Ninguno.

## Assumptions
- Confirmado: Change 1 y change 2 ya cerraron que la coleccion inicial no incluye comentarios y que el recorte diario ocurre antes de este punto.
- Confirmado: Change 4 consumira este contexto para decidir elegibilidad, cierre/resolucion y generacion de contenido.
- Inferido: Un indicador simple de degradacion basta en discovery; la forma exacta del campo puede definirse en SDD.
- Pendiente: Ninguno.

## Open Decisions
- Pendiente: Revisar en proposal/spec/design la cobertura real del raw de comentarios por provider y producir una recomendacion explicita sobre expectativas de profundidad/shape (por ejemplo, top-level, replies, orden, campos faltantes) sin convertir esa revision en bloqueo de discovery.
- Pendiente: Definir en SDD la forma exacta del indicador simple de degradacion y del contrato normalizado, respetando que siga siendo contexto bruto y no resumen editorial.

## Risks
- Confirmado: Si este change empieza a decidir cierre del hilo o valor de respuesta, invadira responsabilidades de IA y mezclara extraccion con juicio editorial.
- Confirmado: Si se fuerza una profundidad de comentarios no confirmada documentalmente, se convertiria una duda de implementacion en un requisito falso.
- Confirmado: Si la degradacion no queda visible, aguas abajo se podria tratar contexto parcial como si fuera completo.

## Readiness for SDD
Status: ready-for-sdd
Reason: El problema, objetivo, actor, trigger, flujo principal, reglas de negocio, limites de alcance y criterios de aceptacion ya estan suficientemente cerrados. La unica duda abierta relevante es revisar en SDD la cobertura real del raw por provider para recomendar profundidad/shape del contrato, pero eso no bloquea discovery porque no cambia el outcome funcional confirmado: extraer y normalizar contexto bruto con degradacion explicita, dejando el juicio editorial para change 4.
