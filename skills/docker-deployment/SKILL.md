---
name: docker-deployment
description: >
  Patrón de despliegue Docker para auto-reddit: contenedor efímero, volúmenes, configuración y cron externo.
  Trigger: Cuando se trabaje en Dockerfile, docker-compose.yml o despliegue en VPS.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use
- Cuando se modifique el Dockerfile o docker-compose.yml
- Cuando se configure el despliegue en VPS
- Cuando se trabaje con volúmenes o persistencia Docker
- Cuando se configure el cron externo

## Critical Patterns

### Modelo operativo
- Contenedor efímero: arranca, ejecuta y muere
- NO hay proceso persistente corriendo 24/7
- Cron externo en el VPS lanza el contenedor cada día
- `restart: "no"` en docker-compose.yml

### Imagen base
- `python:3.14-slim`
- uv instalado desde imagen oficial `ghcr.io/astral-sh/uv:latest`
- Entrypoint: `uv run python -m auto_reddit.main`

### Volúmenes
- SQLite en volumen Docker montado en `/data/`
- La base de datos DEBE persistir entre ejecuciones del contenedor
- Sin el volumen, se pierde la memoria de posts ya enviados

### Variables de entorno
- Desde `.env` vía docker-compose
- NUNCA hardcodear secretos en el Dockerfile
- Variables requeridas: `DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `REDDIT_API_KEY`

### Estructura del Dockerfile
```dockerfile
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --frozen --no-dev
ENTRYPOINT ["uv", "run", "python", "-m", "auto_reddit.main"]
```

### Cron en VPS
Ejemplo de crontab:
```bash
# Ejecutar auto-reddit cada día a las 08:00 UTC
0 8 * * * cd /path/to/auto-reddit && docker compose run --rm auto-reddit >> /var/log/auto-reddit.log 2>&1
```

### Logs
- Solo stdout dentro del contenedor
- Capturar con `docker logs` o redirigir desde cron
- No montar volumen de logs en v1

## Commands
```bash
docker compose build                    # construir imagen
docker compose run --rm auto-reddit     # ejecutar manualmente
docker compose logs auto-reddit         # ver logs última ejecución
docker volume ls                        # verificar volumen SQLite
```

## Resources
- **Arquitectura**: Ver `docs/architecture.md`
- **Operations runbook**: Ver `docs/operations.md`
