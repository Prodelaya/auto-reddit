# Product Discovery Brief: connect-or-remove-half-landed-logic

## Problem Statement
- Confirmed: El repo conserva marcadores históricos de la fase de ensamblaje incremental dentro de código activo: comentarios tipo `# Change N` y docstrings que referencian etapas históricas en lugar de responsabilidades estables del sistema.
- Confirmed: `src/auto_reddit/main.py` narra el pipeline con etiquetas `# Change 1` a `# Change 5` en comentarios de bloque, cuando esos changes ya están archivados y el flujo es producto operativo completo.
- Confirmed: `src/auto_reddit/shared/contracts.py` contiene tres referencias a etapas históricas: la docstring de `is_complete` menciona `(change 1)`, la docstring de `ThreadContext` dice `Salida del paso de extracción de contexto (Change 3)`, y hay dos separadores de sección `# Change 4: ...` y `# Change 5: ...`.
- Confirmed: `src/auto_reddit/reddit/comments.py` contiene referencias históricas similares: el docstring de `fetch_thread_contexts` referencia `(Change 2)` para describir el paso upstream.
- Confirmed: Estos marcadores no rompen el runtime, pero hacen que el código activo funcione como diario histórico de construcción en lugar de expresar la arquitectura presente del sistema.

## Goal / Desired Outcome
- Confirmed: Eliminar todos los marcadores históricos tipo `# Change N` del código activo (comentarios, separadores de sección, docstrings).
- Confirmed: Reescribir cada punto afectado en términos de la responsabilidad presente del sistema, no de la etapa de implementación en que se introdujo.
- Confirmed: La regla de decisión es simple: si el comentario solo aporta historia de construcción, se elimina o se reescribe como responsabilidad actual; si aporta contexto operativo real, se reescribe sin la referencia al change number.
- Inferred: El resultado es un cuerpo de código activo que un nuevo mantenedor puede leer sin necesitar el historial de SDD para entender qué hace cada parte.

## Primary Actor(s)
- Confirmed: Desarrollo/mantenimiento del repo.

## Stakeholders
- Desarrollo
- Responsables de onboarding técnico

## Trigger
- Confirmed: Se detectan comentarios, docstrings o separadores en código activo que referencian etapas históricas de construcción (`# Change N`) en lugar de responsabilidades vigentes del sistema.

## Main Flow
1. Inventariar todos los marcadores históricos tipo `# Change N` en código activo (no en archivos de historial/docs).
2. Para cada marcador: eliminar si solo aporta historia, o reescribir en términos de responsabilidad presente si también aporta contexto operativo.
3. Verificar que el código activo resultante expresa responsabilidades del sistema sin referencias a etapas históricas de implementación.

## Alternative Flows / Edge Cases
- Confirmed: El historial de cambios puede seguir existiendo en OpenSpec, TFM o archivos históricos; lo que se limpia aquí es exclusivamente código activo (`.py`).
- Confirmed: La limpieza de artefactos históricos fuera de código activo no entra aquí; pertenece a `docs-information-architecture-cleanup`.
- Confirmed: Si un comentario aporta contexto operativo imprescindible, se mantiene solo si se reescribe como responsabilidad actual y sin referencia al number de change.

## Business Rules
- Confirmed: Este change no es limpieza documental general; se limita a código activo Python y a marcadores históricos tipo `# Change N` específicamente.
- Confirmed: No debe cambiar comportamiento funcional; es limpieza textual de comentarios y docstrings únicamente.
- Confirmed: Debe venir después de `settings-govern-runtime` para no retirar conceptos que todavía necesiten consolidación de contrato.
- Confirmed: El scope se limita a los tres archivos identificados con marcadores: `main.py`, `shared/contracts.py`, `reddit/comments.py`.

## Permissions / Visibility
- Confirmed: Cambio interno de mantenibilidad.

## Scope In
- Confirmed: `src/auto_reddit/main.py` — comentarios de bloque `# Change 1` a `# Change 5`.
- Confirmed: `src/auto_reddit/shared/contracts.py` — `(change 1)` en docstring de `is_complete`, `(Change 3)` en docstring de `ThreadContext`, `# Change 4:` y `# Change 5:` como separadores de sección.
- Confirmed: `src/auto_reddit/reddit/comments.py` — `(Change 2)` en docstring de `fetch_thread_contexts`.

## Scope Out
- Confirmed: Limpieza de TFM, README o mapa documental amplio.
- Confirmed: Limpieza de artefactos históricos en OpenSpec o docs; eso vive en `docs-information-architecture-cleanup`.
- Confirmed: Redefinición de producto o cambio de comportamiento funcional.
- Confirmed: Hardening operacional o CI.
- Confirmed: Cualquier archivo fuera de los tres identificados arriba.

## Acceptance Criteria
- [ ] Existe un inventario cerrado y exhaustivo de marcadores históricos `# Change N` en código activo.
- [ ] Todos los marcadores del inventario han sido eliminados o reescritos como responsabilidades presentes.
- [ ] `main.py` no contiene ningún comentario `# Change N`; cada bloque se describe por su responsabilidad operativa.
- [ ] `shared/contracts.py` no contiene separadores `# Change N:` ni referencias en docstrings a etapas históricas.
- [ ] `reddit/comments.py` no contiene referencias a etapas históricas en docstrings.
- [ ] El comportamiento funcional del pipeline no cambia (tests existentes pasan sin modificación).
- [ ] Ningún comentario que describa contexto operativo real se ha eliminado; solo los marcadores históricos o los que únicamente comunicaban historia de construcción.

## Non-Functional Notes
- Confirmed: El valor principal es legibilidad arquitectónica y menor deuda conceptual para mantenedores futuros.
- Confirmed: Es un change pequeño y textual; no hay riesgo de regresión funcional si el scope se respeta.

## Assumptions
- Confirmed: El inventario de los tres archivos está cerrado; no hay otros archivos con el mismo patrón (verificado en la exploración).
- Confirmed: La mayor parte del historial de construcción debe conservarse fuera del código activo (en OpenSpec/TFM).

## Open Decisions
- Ninguna.

## Risks
- Confirmed: Si el inventario se amplía sin control, este change puede invadir limpieza documental general. La regla de cierre es: solo los tres archivos identificados.
- Inferred: Si se pospone demasiado, el código activo seguirá mezclando historia del repo con responsabilidades presentes, dificultando el onboarding.

## Readiness for SDD
Status: ready-for-sdd
Reason: Inventario cerrado y exhaustivo con archivos y ubicaciones exactas identificadas. Regla de decisión clara. Scope explícito y acotado a tres archivos. Separación explícita frente a `docs-information-architecture-cleanup`. No hay ambigüedad sobre qué entra y qué no entra.
