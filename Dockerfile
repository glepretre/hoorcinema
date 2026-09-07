FROM node:24-alpine AS frontend

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.12.10 AS uv

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST_DIR=/app/frontend_dist \
    PATH=/app/.venv/bin:$PATH

COPY --from=uv /uv /bin/
WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./
COPY --from=frontend /app/dist/ /app/frontend_dist/

CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile - --error-logfile -"]
