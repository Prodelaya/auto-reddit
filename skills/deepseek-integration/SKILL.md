---
name: deepseek-integration
description: >
  Patrón de integración con DeepSeek vía SDK de OpenAI para auto-reddit: conexión, structured output con Pydantic y manejo de errores.
  Trigger: Cuando se implemente o modifique la conexión con DeepSeek o la evaluación IA.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use
- Cuando se implemente la evaluación IA de oportunidades
- Cuando se modifique el prompt o las reglas de respuesta
- Cuando se conecte con la API de DeepSeek
- Cuando se defina structured output del LLM

## Critical Patterns

### Conexión
- SDK de OpenAI apuntando a DeepSeek
- Base URL: `https://api.deepseek.com`
- API key desde `config/settings.py` (pydantic-settings)
- NUNCA hardcodear la key

Ejemplo mínimo:
```python
from openai import OpenAI
from auto_reddit.config.settings import settings

client = OpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
)
```

### Structured Output
- Definir el schema de respuesta con Pydantic
- La IA debe devolver JSON parseable directamente por el modelo Pydantic
- Usar `response_format` del SDK para forzar structured output

Ejemplo:
```python
from pydantic import BaseModel

class OpportunityEvaluation(BaseModel):
    suggest: bool
    opportunity_type: str | None = None
    post_summary: str | None = None
    thread_summary: str | None = None
    suggested_response: str | None = None
```

### Manejo de errores
- Retry en errores transitorios (rate limit, timeout)
- Fallar explícitamente en errores permanentes (auth, bad request)
- Loguear errores a stdout
- NUNCA silenciar excepciones de la API

### Reglas de comportamiento
- El estilo y criterios de la IA se documentan en `docs/product/ai-style.md`
- El prompt debe alinearse con esas reglas, no inventar otras
- La IA puede devolver `NO_SUGERIR` si no hay aportación útil

## Commands
```bash
uv run python -c "from openai import OpenAI; print('SDK OK')"  # verificar SDK
```

## Resources
- **Estilo IA**: Ver `docs/product/ai-style.md`
- **Arquitectura**: Ver `docs/architecture.md`
- **Producto**: Ver `docs/product/product.md`
