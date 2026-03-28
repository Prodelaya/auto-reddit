# Product Discovery Brief: connect-or-remove-half-landed-logic

## Problem Statement
- Confirmed: El repo todavia conserva restos runtime-adjacent de la fase de ensamblaje incremental que hoy ya no representan bien el sistema final.
- Confirmed: `src/auto_reddit/main.py` sigue narrando el pipeline por "Change 1/2/3/4/5" en comentarios internos aunque esos changes ya estan archivados y el flujo ya es producto operativo completo.
- Confirmed: `src/auto_reddit/shared/contracts.py` sigue etiquetando zonas del contrato por "Change 4" y "Change 5", lo que mantiene una semantica de transicion en una capa que deberia describir responsabilidades estables.
- Inferred: Estos restos no rompen el runtime por si solos, pero dejan logica y contratos con semantica medio aterrizada: hablan del camino historico de construccion, no de la arquitectura viva del sistema.

## Goal / Desired Outcome
- Confirmed: Conectar o eliminar artefactos runtime-adjacent que hoy sugieren una transicion ya superada.
- Confirmed: La regla de decision es simple: conectar solo si aporta valor operativo claro; en caso contrario, eliminar.
- Confirmed: La capa viva del codigo debe hablar en terminos de responsabilidades estables, no de etapas historicas de implementacion.
- Inferred: El change debe dejar menos superficie conceptual falsa para el proximo mantenimiento.

## Primary Actor(s)
- Confirmed: Desarrollo/mantenimiento del repo.

## Stakeholders
- Desarrollo
- Responsables de onboarding tecnico

## Trigger
- Confirmed: Se detecta un concepto, comentario o contrato dentro de codigo activo que ya no representa una responsabilidad vigente sino una etapa historica intermedia.

## Main Flow
1. Inventariar restos runtime-adjacent de logica o semantica de transicion en codigo activo.
2. Clasificar cada item: conectar a una responsabilidad vigente o eliminarlo.
3. Dejar el codigo activo expresando responsabilidades presentes del sistema, no hitos historicos.

## Alternative Flows / Edge Cases
- Confirmed: El historico de cambios puede seguir existiendo en OpenSpec, TFM o archivos historicos; lo que se limpia aqui es codigo activo y contratos vivos.
- Confirmed: La limpieza de artefactos historicos fuera de codigo activo no entra aqui; pertenece a `docs-information-architecture-cleanup`.
- Inferred: Si algun comentario historico sigue aportando contexto operativo imprescindible, puede mantenerse solo si se reescribe como responsabilidad actual y no como etapa de change.

## Business Rules
- Confirmed: Este change no es limpieza documental general; se limita a codigo activo y conceptos runtime-adjacent.
- Confirmed: No debe cambiar comportamiento funcional salvo donde un artefacto medio aterrizado tenga que conectarse realmente o eliminarse.
- Confirmed: Debe venir despues de `settings-govern-runtime` para no retirar conceptos que todavia necesiten consolidacion de contrato.
- Confirmed: El scope se limita a logica medio aterrizada que siga activa hoy; artefactos puramente historicos se derivan al change documental.

## Permissions / Visibility
- Confirmed: Cambio interno de mantenibilidad.
- Pending: Ninguno.

## Scope In
- Confirmed: Comentarios y etiquetas de codigo activo que siguen expresando el sistema por numero de change en vez de por responsabilidad estable.
- Confirmed: Conceptos runtime-adjacent medio aterrizados cuya semantica actual sea transicional y no viva.
- Confirmed: Solo items activos cuya conexion o eliminacion cambie positivamente la claridad operativa del sistema.

## Scope Out
- Confirmed: Limpieza de TFM, README o mapa documental amplio.
- Confirmed: Limpieza de artefactos historicos aunque esten mal organizados; eso vive en `docs-information-architecture-cleanup`.
- Confirmed: Redefinicion de producto.
- Confirmed: Hardening operacional o CI.

## Acceptance Criteria
- [ ] Existe un inventario cerrado de restos runtime-adjacent medio aterrizados en codigo activo.
- [ ] Cada item del inventario queda conectado a una responsabilidad vigente o eliminado.
- [ ] `main.py` y los contratos compartidos dejan de depender de la narrativa por numero de change para explicarse.
- [ ] El resultado reduce ambiguedad conceptual sin mover limpieza documental general a este change.
- [ ] Ningun item permanece solo por valor historico; si no aporta valor operativo claro, sale de codigo activo.

## Non-Functional Notes
- Confirmed: El valor principal es legibilidad arquitectonica y menor deuda conceptual.
- Inferred: Es un change pequeno pero importante para evitar que el codigo activo funcione como diario historico.

## Assumptions
- Confirmed: Hay evidencia suficiente para justificar un change separado sin mezclarlo con docs cleanup.
- Confirmed: La mayor parte del historico debe conservarse fuera del codigo activo.

## Open Decisions
- Ninguna.

## Risks
- Confirmed: Si el inventario no se cierra bien, este change puede invadir limpieza documental general.
- Inferred: Si se pospone demasiado, el codigo activo seguira mezclando historia del repo con responsabilidades presentes.

## Readiness for SDD
Status: ready-for-sdd
Reason: La regla de decision, el foco en logica activa y la separacion explicita frente a `docs-information-architecture-cleanup` ya cierran la frontera del change y evitan solape innecesario.
