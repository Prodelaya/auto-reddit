## Entorno y dependencias
- Usar `uv` (no pip): `uv sync` para instalar, `uv run <cmd>` para ejecutar
- Python 3.14 requerido (gestionado por `.python-version` + uv)
- Variables de entorno: copiar `.env.example` a `.env` y rellenar `DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `REDDIT_API_KEY`

## Build y test
- Tests: `uv run pytest tests/ -x --tb=short`
- No hay Makefile ni scripts auxiliares; uv es la única interfaz

## Restricciones
- No publicar en Reddit de forma autónoma — el sistema es solo de detección, el humano decide
- No modificar `.env` directamente; usar `.env.example` como referencia
- El paquete vive en `src/auto_reddit/` (hatchling src-layout)

## Skills del proyecto

| Skill | Descripción | Trigger | Ruta |
|---|---|---|---|
| `python-conventions` | Convenciones de código Python: arquitectura modular, contratos Pydantic, configuración y estilo | Cuando se escriba o revise código Python | [SKILL.md](skills/python-conventions/SKILL.md) |
| `deepseek-integration` | Integración con DeepSeek vía SDK de OpenAI: conexión, structured output y manejo de errores | Cuando se implemente o modifique la evaluación IA | [SKILL.md](skills/deepseek-integration/SKILL.md) |
| `docker-deployment` | Despliegue Docker: contenedor efímero, volúmenes, configuración y cron externo | Cuando se trabaje en Dockerfile, docker-compose o despliegue | [SKILL.md](skills/docker-deployment/SKILL.md) |
