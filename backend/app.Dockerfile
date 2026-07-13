FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /backend

COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --locked --no-dev --group api

COPY src/__init__.py ./src/__init__.py
COPY src/core ./src/core
COPY src/db ./src/db
COPY src/app ./src/app
COPY alembic.ini ./
COPY migrations ./migrations
COPY entrypoint.app.sh ./entrypoint.app.sh
RUN chmod +x ./entrypoint.app.sh

ENV RUN_MIGRATIONS=1
ENTRYPOINT ["/backend/entrypoint.app.sh"]
