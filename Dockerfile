FROM python:3.12-slim

# Evita archivos .pyc y permite ver logs inmediatamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Instalar dependencias primero para aprovechar la cache de Docker
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# Copiar el código después de las dependencias
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]