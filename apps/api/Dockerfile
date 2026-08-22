FROM python:3.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /workspace/apps/api
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app app

FROM base AS dependencies
COPY apps/api/pyproject.toml ./pyproject.toml
RUN python -m pip install --no-cache-dir --upgrade pip==26.0.1 \
    && python -m pip install --no-cache-dir ".[test]"

FROM dependencies AS development
COPY --chown=app:app apps/api ./
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM dependencies AS runtime
COPY --chown=app:app apps/api ./
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

