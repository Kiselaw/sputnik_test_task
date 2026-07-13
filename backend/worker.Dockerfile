FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /backend

COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --locked --no-dev --group worker

COPY src/__init__.py ./src/__init__.py
COPY src/core ./src/core
COPY src/db ./src/db
COPY src/worker ./src/worker
COPY src/app/__init__.py ./src/app/__init__.py
COPY src/app/alerts/__init__.py ./src/app/alerts/__init__.py
COPY src/app/alerts/repository.py ./src/app/alerts/repository.py
COPY src/app/files/__init__.py ./src/app/files/__init__.py
COPY src/app/files/constants.py ./src/app/files/constants.py
COPY src/app/files/repository.py ./src/app/files/repository.py
COPY src/app/files/storage.py ./src/app/files/storage.py
COPY entrypoint.worker.sh ./entrypoint.worker.sh
RUN chmod +x ./entrypoint.worker.sh

ENTRYPOINT ["/backend/entrypoint.worker.sh"]
