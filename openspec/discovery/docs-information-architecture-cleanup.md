# Product Discovery Brief: docs-information-architecture-cleanup

## Problem Statement
- Confirmed: El repo contiene varias capas documentales con distinta caducidad (`docs/`, `openspec/`, `TFM/`) y no toda la informacion vigente, historica y de planning esta separada de forma suficientemente obvia para el siguiente lector.
- Confirmed: `docs/README.md` ya advierte que existen ideas historicas superadas, pero la guia extensa en `TFM/guia-didactica-auto-reddit.md` aun mezcla valor vigente, historico, pendientes antiguos y narrativa de implementacion.
- Confirmed: La peticion del usuario incluye una prioridad explicita de limpieza documental / arquitectura de informacion como change separado.
- Inferred: Sin una IA documental clara, el repo fuerza al lector a distinguir manualmente entre verdad operativa, historia del proyecto y material de aprendizaje.

## Goal / Desired Outcome
- Confirmed: Reordenar la documentacion para que la verdad vigente, el historico y el planning queden claramente separados y navegables.
- Confirmed: El resultado debe hacer mas facil encontrar "que manda hoy" sin perder trazabilidad historica.
- Inferred: La limpieza documental debe consolidar, no duplicar, la verdad que quede cerrada por los changes previos de runtime/config/operacion.

## Primary Actor(s)
- Confirmed: Cualquier persona que entra a leer o mantener el repositorio.
- Inferred: Futuro agente o desarrollador que necesita saber donde esta la verdad vigente sin recorrer todo el historico.

## Stakeholders
- Desarrollo
- Operaciones
- Documentacion / onboarding

## Trigger
- Confirmed: Necesidad de navegar el repo sin confundir verdad vigente, historia y planning.

## Main Flow
1. Identificar los artefactos documentales por tipo: verdad vigente, planeamiento, historico, didactico.
2. Redefinir una arquitectura de informacion simple para esas capas.
3. Reubicar, resumir o enlazar el contenido para que cada capa tenga un papel claro.
4. Dejar un mapa documental de entrada inequívoco.

## Alternative Flows / Edge Cases
- Confirmed: El material historico y didactico puede mantenerse; el objetivo no es borrarlo, sino ubicarlo y etiquetarlo correctamente.
- Inferred: Algunas contradicciones se resolveran simplemente enlazando a la fuente de verdad correcta, no reescribiendo todos los documentos.

## Business Rules
- Confirmed: La verdad vigente debe seguir anclada en pocos artefactos canonicamente identificables.
- Confirmed: El historico no debe competir con la verdad vigente en las rutas de lectura principales.
- Confirmed: Este change va al final porque debe consolidar decisiones ya cerradas por los changes anteriores.

## Permissions / Visibility
- Confirmed: Cambio interno de documentacion e informacion.
- Pending: Ninguno.

## Scope In
- Confirmed: Mapa documental de entrada.
- Confirmed: Separacion explicita entre verdad vigente, historico y planning.
- Confirmed: Reubicacion o clarificacion de artefactos que hoy inducen a leer material historico como vigente.

## Scope Out
- Confirmed: Cambios funcionales del runtime.
- Confirmed: Hardening operacional.
- Confirmed: CI.
- Confirmed: Limpieza de codigo activo que corresponde a `connect-or-remove-half-landed-logic`.

## Acceptance Criteria
- [ ] Existe una arquitectura de informacion documental explicita y facil de navegar.
- [ ] Queda claro que documentos son verdad vigente, cuales son planning y cuales son historico/didactico.
- [ ] El lector puede llegar a la verdad vigente sin depender de interpretar el historico por su cuenta.
- [ ] La trazabilidad historica se conserva sin competir con la lectura principal.

## Non-Functional Notes
- Confirmed: El valor principal es reducir carga cognitiva y errores de interpretacion.
- Inferred: La limpieza debe favorecer onboarding y mantenimiento futuro.

## Assumptions
- Confirmed: `docs/README.md` ya ofrece una base inicial, pero no es suficiente para ordenar todo el paisaje documental actual.
- Confirmed: Este change debe ejecutarse despues de cerrar los cambios previos para no limpiar sobre una base todavia inestable.

## Open Decisions
- Cerrar si `TFM/guia-didactica-auto-reddit.md` sigue como guia viva, se mueve claramente a historico/didactico, o se parte en varias piezas.
- Cerrar que mapa/documento de entrada sera la puerta principal del repositorio.

## Risks
- Confirmed: Si se hace antes de cerrar runtime/config/operacion, la documentacion se limpiara dos veces.
- Inferred: Si se intenta reescribir todo, el change se volvera demasiado grande; la IA debe priorizar estructura y claridad.

## Readiness for SDD
Status: ready-for-sdd
Reason: El outcome, actor, fronteras y criterios de aceptacion estan claros; las decisiones abiertas son de organizacion concreta del mapa documental, no de descubrimiento adicional del problema.
