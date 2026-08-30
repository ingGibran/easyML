# syntax=docker/dockerfile:1.7
FROM python:3.12.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

# [SOLUCIÓN AQUÍ]: Instalamos libpq5 a nivel del sistema operativo para psycopg
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Pin the uv image version
COPY --from=ghcr.io/astral-sh/uv:0.4.30 /uv /uvx /bin/

# Configurar el usuario
RUN groupadd -r app && useradd -r -g app -m -d /home/app app \
    && mkdir -p /tmp/uv-cache /home/app /app \
    && chown -R app:app /app /home/app /tmp/uv-cache

USER app

# Copiar dependencias
COPY --chown=app:app pyproject.toml uv.lock ./

# Instalar dependencias
RUN uv sync --frozen --no-dev --no-install-project

# Copiar código fuente
COPY --chown=app:app . .

EXPOSE 8000

# Usamos uv run para garantizar que uvicorn se ejecute dentro del entorno virtual
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]