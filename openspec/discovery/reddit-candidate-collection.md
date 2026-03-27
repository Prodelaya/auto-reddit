# Product Discovery Brief: reddit-candidate-collection

## Problem Statement
- Confirmed: El sistema necesita una primera recoleccion fiable de candidatos desde Reddit para alimentar el flujo diario sin mezclar todavia reglas de unicidad, seleccion limitada ni evaluacion IA.
- Inferred: Separar esta recoleccion como change 1 reduce ambiguedad de alcance y evita acoplar demasiado pronto decisiones de memoria o delivery.
- Pending: None.

## Goal / Desired Outcome
- Confirmed: Recoger TODOS los posts de `r/Odoo` creados en los ultimos 7 dias, priorizados por recencia, sin comentarios, y entregar una lista normalizada en memoria/proceso para el siguiente paso.
- Inferred: La salida debe ser tolerante a respuestas heterogeneas de las APIs de Reddit para no perder candidatos utiles por diferencias de shape.
- Pending: None.

## Primary Actor(s)
- Confirmed: Proceso diario interno de `auto-reddit`.
- Inferred: El consumidor inmediato es el siguiente change del pipeline (`candidate-memory-and-uniqueness`).
- Pending: None.

## Stakeholders
- Equipo de marketing y contenido que recibira oportunidades mas adelante por Telegram.
- Responsable de producto que define alcance y reglas operativas del slice.

## Trigger
- Ejecucion diaria del proceso de `auto-reddit` en un dia habil.

## Main Flow
1. El proceso consulta `r/Odoo`.
2. Recupera posts creados dentro de los ultimos 7 dias.
3. Ordena y prioriza por recencia.
4. Normaliza cada post al contrato minimo compartido.
5. Conserva tambien los posts con campos faltantes, marcandolos como incompletos.
6. Entrega la lista normalizada en memoria/proceso al siguiente paso.

## Alternative Flows / Edge Cases
- Si faltan campos del contrato minimo, el post NO se descarta automaticamente; se conserva con marca de incompleto.
- Si una API devuelve URLs relativas o nombres de campo distintos, la normalizacion debe adaptar el shape sin cambiar el alcance funcional.
- La limitacion a 10 posts NO ocurre en este change; se resuelve aguas abajo.

## Business Rules
- El change se clasifica como `single-change`.
- Solo entran posts de `r/Odoo`.
- Solo entran posts creados en los ultimos 7 dias.
- La prioridad operativa es por recencia.
- Este change NO incluye comentarios.
- El contrato minimo por post es: `post_id`, `title`, `body/selftext`, `url/permalink`, `author`, `subreddit`, `created_at`.
- La salida es una lista normalizada en memoria/proceso, no un backlog persistente.

## Permissions / Visibility
- Uso interno del sistema; no hay interfaz de usuario ni publicacion externa en este change.
- La visibilidad funcional se limita al pipeline interno previo a IA y delivery.

## Scope In
- Recoleccion de posts de `r/Odoo`.
- Filtro temporal por `created_at` dentro de 7 dias.
- Priorizacion por recencia.
- Normalizacion de posts al contrato minimo.
- Marca de incompleto cuando falten campos.
- Entrega al siguiente paso en memoria/proceso.

## Scope Out
- Comentarios del hilo.
- Seleccion limitada a 10 candidatos.
- Exclusiones por `sent` o `rejected`.
- Evaluacion por IA.
- Entrega por Telegram.
- Caso `old but alive`.

## Acceptance Criteria
- [ ] El change recoge posts SOLO de `r/Odoo`.
- [ ] El change conserva todos los posts creados dentro de los ultimos 7 dias.
- [ ] La salida prioriza por recencia.
- [ ] La salida NO incluye comentarios.
- [ ] Cada candidato se entrega con el contrato minimo definido o, si faltan campos, con marca de incompleto.
- [ ] La salida se entrega como lista normalizada en memoria/proceso para el siguiente paso.
- [ ] El recorte a 10 candidatos no ocurre en este change.

## Non-Functional Notes
- La normalizacion debe ser robusta frente a shapes heterogeneos de APIs de Reddit.
- El change debe preservar la maxima cobertura posible dentro del alcance confirmado.

## Assumptions
- La ejecucion diaria ya esta controlada por la orquestacion general del producto.
- La logica de unicidad y memoria se resuelve en el change 2.

## Open Decisions
- None.

## Risks
- Si la documentacion mezcla este change con la seleccion limitada a 10, el alcance se implementaria recortado demasiado pronto.
- Si se descartan posts incompletos en lugar de marcarlos, se puede perder cobertura operativa.

## Readiness for SDD
Status: ready-for-sdd
Reason: El problema, objetivo, flujo principal, reglas de negocio, limites de alcance y criterios de aceptacion del change 1 quedan cerrados sin dependencias funcionales abiertas.
