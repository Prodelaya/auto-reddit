# connect-or-remove-half-landed-logic

Eliminar los marcadores históricos tipo `# Change N` del código activo Python y reescribir cada punto en términos de la responsabilidad presente del sistema.

## Contexto

Durante el ensamblaje incremental del pipeline, los módulos se documentaron con etiquetas tipo `# Change 1`, `# Change 3`, `# Change 4: ...` para narrar el orden de implementación. Esos changes ya están archivados en OpenSpec y el sistema es producto operativo completo. Las etiquetas históricas siguen en el código activo como deuda conceptual: un nuevo mantenedor necesita el historial de SDD para entender el código en lugar de que el código se explique por sí mismo.

## Archivos en scope

| Archivo | Marcadores identificados |
|---------|--------------------------|
| `src/auto_reddit/main.py` | Comentarios `# Change 1` a `# Change 5` en bloques del pipeline |
| `src/auto_reddit/shared/contracts.py` | `(change 1)` en docstring de `is_complete`; `(Change 3)` en docstring de `ThreadContext`; separadores `# Change 4:` y `# Change 5:` |
| `src/auto_reddit/reddit/comments.py` | `(Change 2)` en docstring de `fetch_thread_contexts` |

## Regla de decisión

- Si el comentario **solo aporta historia de construcción** → eliminar.
- Si el comentario **también aporta contexto operativo** → reescribir como responsabilidad presente, sin referencia al number de change.

## Qué NO entra

- Cambios de comportamiento funcional.
- Limpieza de TFM, README o docs fuera de código activo Python.
- Archivos distintos a los tres identificados.
- Limpieza de artefactos históricos en OpenSpec (pertenece a `docs-information-architecture-cleanup`).
