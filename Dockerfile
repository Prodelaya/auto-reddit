FROM python:3.12-slim

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar ficheros de proyecto
COPY pyproject.toml .
COPY src/ src/

# Instalar dependencias de producción
RUN uv pip install --system --no-cache .

ENTRYPOINT ["python", "-m", "auto_reddit.main"]
