---
name: python-conventions
description: >
  Convenciones de código Python para auto-reddit: arquitectura modular, contratos Pydantic, configuración y estilo.
  Trigger: Cuando se escriba o revise código Python en el proyecto.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Cuando se escriba código nuevo en cualquier módulo
- Cuando se revise código existente
- Cuando se creen contratos entre módulos
- Cuando se añadan dependencias o configuración

## Critical Patterns

### Arquitectura modular

- Monolito modular con contratos explícitos
- Ningún módulo importa a otro módulo directamente
- Los módulos solo importan de `shared/` y de `config/`
- `main.py` es el único que conoce a todos los módulos y los conecta

### Estructura de módulos

```
src/auto_reddit/
├── reddit/          # extracción de candidatos y contexto
├── evaluation/      # evaluación IA con DeepSeek
├── delivery/        # entrega por Telegram
├── persistence/     # memoria operativa SQLite
├── shared/          # contratos Pydantic compartidos
├── config/          # settings con pydantic-settings
└── main.py          # orquestador del proceso diario
```

### Contratos

- Pydantic para TODOS los contratos entre módulos
- Definidos en `shared/contracts.py`
- Validación automática de tipos y estructura
- Serialización JSON vía `.model_dump()`

### Configuración

- pydantic-settings con `.env`
- Validación al arrancar: si falta una variable, el proceso no empieza
- Parámetros de producto configurables en `config/settings.py`
- NUNCA hardcodear valores que deban ser configurables

### Dependencias

- Gestor: `uv` (NUNCA pip)
- `uv sync` para instalar
- `uv run <cmd>` para ejecutar
- `uv.lock` se commitea siempre

### Testing

- pytest como framework
- Tests en `tests/test_{modulo}/`
- Ejecutar con `uv run pytest tests/ -x --tb=short`

### Logging

- Solo stdout
- Nivel mínimo útil: contadores de decisiones + errores
- Usar `logging` stdlib, no print

### Límites de responsabilidad

| Módulo | Responsabilidad | NO hace |
|---|---|---|
| `reddit/` | Conectar con APIs, traer posts y comentarios, normalizar al contrato compartido. | NO decide si un post es oportunidad, NO filtra, NO evalúa, NO guarda estado. |
| `evaluation/` | Recibir candidatos normalizados, conectar con DeepSeek (via SDK de OpenAI), aplicar reglas de elegibilidad, devolver resultado estructurado. | NO trae posts, NO envía a Telegram, NO guarda estado. |
| `delivery/` | Recibir oportunidades evaluadas, formatear mensajes, enviar a Telegram. | NO evalúa, NO filtra, NO decide qué se envía. |
| `persistence/` | Guardar/consultar/purgar registros de posts procesados, gestionar 3 estados, aplicar TTL. | NO conecta con Reddit, NO evalúa, NO envía. |
| `shared/` | Contratos Pydantic compartidos, tipos comunes. | NO contiene lógica de negocio. |
| `config/` | Settings con pydantic-settings, carga de `.env`. | NO contiene lógica. |
| `main.py` | Orquesta el flujo diario completo. | NO contiene lógica de negocio de ningún módulo. |

## Commands

```bash
uv sync                              # instalar dependencias
uv run pytest tests/ -x --tb=short   # ejecutar tests
uv run python -m auto_reddit.main    # ejecutar proceso
uv lock                              # regenerar lockfile
```

## Resources

- **Arquitectura**: Ver `docs/architecture.md`
- **Producto**: Ver `docs/product/product.md`
