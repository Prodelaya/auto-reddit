FROM python:3.14-slim

LABEL org.opencontainers.image.title="auto-reddit" \
      org.opencontainers.image.description="Detección diaria de oportunidades en Reddit para equipos Odoo" \
      org.opencontainers.image.source="https://github.com/pablomata/auto-reddit"

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar ficheros de proyecto
COPY pyproject.toml .
COPY src/ src/

# Instalar dependencias de producción
RUN uv pip install --system --no-cache .

ENTRYPOINT ["python", "-m", "auto_reddit.main"]
