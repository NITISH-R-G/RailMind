FROM python:3.12-slim as builder

WORKDIR /app

COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels pydantic pydantic-settings prometheus-client python-json-logger tenacity langchain-community httpx langchain-anthropic langchain-ollama

FROM python:3.12-slim

RUN useradd -m -s /bin/bash appuser

WORKDIR /app

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY backend/ /app/backend/

RUN mkdir -p /var/log/railmind && chown -R appuser:appuser /var/log/railmind

USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
