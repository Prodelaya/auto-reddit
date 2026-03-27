# Product Discovery Brief: candidate-memory-and-uniqueness

## Classification
- Confirmado: El trabajo se clasifica como `single-change` porque resuelve un unico resultado funcional coherente: aplicar memoria operativa minima y unicidad para el slice diario sin convertirlo en backlog editorial ni en iniciativa separada.
- Inferido: Este cambio es el consumidor natural de `reddit-candidate-collection` y deja fuera tanto la recoleccion inicial como cualquier diseno tecnico de retries o delivery.
- Pendiente: Ninguno.

## Problem Statement
- Confirmado: El sistema necesita evitar duplicados, recordar decisiones finales por post y soportar que una oportunidad aceptada por IA pueda reintentarse en Telegram sin volver a evaluarse.
- Inferido: Sin esta capa, el flujo diario mezclaria seleccion, delivery y memoria de forma ambigua, con riesgo de reenvios duplicados o de perder oportunidades ya aceptadas por IA cuando falle Telegram.
- Pendiente: Ninguno.

## Goal / Desired Outcome
- Confirmado: Excluir antes de la revision los posts ya decididos como `sent` o `rejected`, revisar cada dia solo los 8 elegibles mas recientes y persistir un minimo operativo que permita reintentar delivery tras aceptacion de IA sin reevaluacion.
- Inferido: La memoria debe quedarse en el minimo necesario para el primer slice: decisiones finales mas una persistencia operacional transitoria previa a `sent`, sin convertirse en historico amplio ni cola editorial.
- Pendiente: Ninguno.

## Primary Actor(s)
- Confirmado: Proceso diario interno de `auto-reddit`.
- Inferido: El resultado funcional sirve al equipo de marketing y contenido al garantizar que Telegram reciba oportunidades unicas y consistentes.
- Pendiente: Ninguno.

## Stakeholders
- Equipo de marketing y contenido que recibe las oportunidades en Telegram.
- Responsable de producto que fija la regla de unicidad, el corte diario y la semantica de estados.

## Trigger
- Confirmado: Ejecucion diaria del proceso en un dia habil, despues de recibir la lista normalizada del change `reddit-candidate-collection`.
- Inferido: La decision final `sent` solo puede cerrarse tras exito real de delivery en Telegram.
- Pendiente: Ninguno.

## Main Flow
1. El proceso recibe los candidatos normalizados del change anterior.
2. Excluye los posts ya persistidos con decision final `sent` o `rejected`.
3. Toma los 8 posts elegibles mas recientes por `created_at` para la revision diaria.
4. Evalua cada post con IA para decidir si es oportunidad valida.
5. Si la IA concluye rechazo final de negocio, persiste `rejected` y el post deja de competir.
6. Si la IA acepta una oportunidad, persiste una situacion operacional transitoria y minima que conserva la oportunidad lista para retry de delivery sin reevaluacion.
7. Intenta el envio por Telegram.
8. Solo si Telegram entrega correctamente, registra `sent` como decision final y el post deja de competir definitivamente.

## Alternative Flows / Edge Cases
- Confirmado: Si un post no se selecciona hoy pero sigue dentro de la ventana de 7 dias y no esta marcado como `sent` ni `rejected`, manana vuelve a competir normalmente; `not selected today` no se persiste.
- Confirmado: Si Telegram falla despues de una aceptacion de IA, el sistema conserva la persistencia operacional minima necesaria para reintentar el delivery sin reevaluar IA.
- Inferido: La persistencia transitoria previa a `sent` debe distinguirse claramente de los estados finales de negocio para no marcar como enviado algo que aun no llego a Telegram.
- Pendiente: Ninguno.

## Business Rules
- Confirmado: El change se clasifica como `single-change`.
- Confirmado: No existe estado `approved` ni backlog editorial explicito.
- Confirmado: El corte aguas abajo es de 8 posts elegibles por dia, no 10.
- Confirmado: `sent` es una decision final y ocurre SOLO tras entrega exitosa en Telegram.
- Confirmado: `rejected` es una decision final de negocio tomada por IA y el post no vuelve a procesarse.
- Confirmado: `not selected today` no es un estado persistente.
- Confirmado: Debe existir una persistencia operacional transitoria, distinta de las decisiones finales, para soportar retry-readiness despues de aceptacion IA y antes de `sent`.
- Confirmado: La persistencia de este change queda limitada a decisiones finales mas el minimo pre-send necesario para retry sin reevaluacion.
- Inferido: La semantica funcional importante es la separacion entre estado final de negocio y estado operacional previo a envio; el nombre exacto de ese estado no condiciona esta discovery.
- Pendiente: Ninguno.

## Permissions / Visibility
- Confirmado: Uso interno del sistema; no introduce interfaz humana de backlog ni acciones manuales sobre estados.
- Inferido: La visibilidad funcional externa sigue siendo solo Telegram cuando el delivery tiene exito.
- Pendiente: Ninguno.

## Scope In
- Confirmado: Exclusiones por memoria operativa minima usando decisiones finales `sent` y `rejected`.
- Confirmado: Seleccion diaria de los 8 posts elegibles mas recientes por `created_at`.
- Confirmado: Persistencia de `rejected` cuando la IA resuelve descarte final de negocio.
- Confirmado: Persistencia transitoria minima para oportunidades aceptadas por IA pendientes de delivery final.
- Confirmado: Cierre en `sent` solo tras envio correcto a Telegram.
- Confirmado: Retry-readiness a nivel funcional, sin reevaluacion IA tras aceptacion previa.

## Scope Out
- Confirmado: Recoleccion inicial de posts desde Reddit.
- Confirmado: Comentarios del hilo como parte de la discovery de memoria.
- Confirmado: Backlog editorial, cola manual o estado `approved`.
- Confirmado: Persistencia de `not selected today`.
- Confirmado: Diseno tecnico del mecanismo de retry, delivery o almacenamiento.
- Confirmado: Historico largo, analitica o seguimiento ampliado de posts.

## Acceptance Criteria
- [ ] El change excluye antes de la revision diaria los posts ya decididos como `sent` o `rejected`.
- [ ] El change revisa cada dia solo los 8 posts elegibles mas recientes por `created_at`.
- [ ] Si la IA rechaza un post como decision final de negocio, el post queda persistido como `rejected` y no vuelve a competir.
- [ ] Si la IA acepta una oportunidad y Telegram aun no ha entregado correctamente, el sistema conserva una persistencia operacional minima distinta de `sent` para permitir retry sin reevaluacion IA.
- [ ] `sent` solo se registra despues de una entrega correcta en Telegram.
- [ ] Un fallo de Telegram despues de aceptacion IA no provoca nueva evaluacion por IA.
- [ ] Un post no seleccionado en una ejecucion sigue pudiendo competir en dias posteriores mientras siga dentro de 7 dias y no tenga decision final.
- [ ] El change no introduce backlog editorial ni un estado `approved`.

## Non-Functional Notes
- Confirmado: La persistencia debe mantenerse minima para respetar el alcance del primer slice.
- Inferido: La semantica de estados debe ser simple y consistente para que unicidad e idempotencia no dependan de interpretaciones ambiguas.
- Pendiente: Ninguno.

## Assumptions
- Confirmado: `reddit-candidate-collection` ya entrega la lista normalizada completa y este change trabaja aguas abajo sobre esa salida.
- Confirmado: Telegram sigue siendo el unico canal de entrega del slice.
- Inferido: La necesidad funcional de retry-readiness existe aunque el detalle tecnico del retry se defina mas adelante.
- Pendiente: Ninguno.

## Open Decisions
- Pendiente: El nombre documental exacto de la persistencia operacional transitoria previa a `sent` puede decidirse en SDD siempre que preserve esta semantica: no es estado final de negocio, pero si permite retry sin reevaluacion IA.

## Risks
- Confirmado: Si `sent` se registrara antes del exito real en Telegram, se perderian oportunidades validas por falsos positivos de entrega.
- Confirmado: Si no existiera persistencia transitoria tras aceptacion IA, un fallo de Telegram obligaria a reevaluar o podria duplicar decisiones.
- Confirmado: Si se introduce un backlog editorial o un estado `approved`, el alcance del primer slice se inflaria y se mezclarian responsabilidades no confirmadas.

## Readiness for SDD
Status: ready-for-sdd
Reason: El cambio ya tiene cerrados problema, objetivo, actor, trigger, flujo principal, reglas de negocio, limites de alcance y criterios de aceptacion. Solo queda pendiente un detalle de nomenclatura no bloqueante sobre como llamar documentalmente a la persistencia operacional transitoria previa a `sent`.
