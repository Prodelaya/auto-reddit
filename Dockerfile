FROM python:3.14-slim

LABEL org.opencontainers.image.title="auto-reddit" \
      org.opencontainers.image.description="Detección diaria de oportunidades en Reddit para equipos Odoo" \
      org.opencontainers.image.source="https://github.com/Prodelaya/auto-reddit"

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar ficheros de proyecto (uv.lock garantiza build reproducible)
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Instalar dependencias de producción desde lockfile (reproducible, sin dev deps)
RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "python", "-m", "auto_reddit.main"]
