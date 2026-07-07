# Multi-stage Dockerfile for FastAPI Backend
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN groupadd -r railmind && useradd -r -g railmind railmind

WORKDIR /app

COPY --from=builder /root/.local /home/railmind/.local
COPY . .

# Ensure log directory exists and is writable by non-root user
RUN mkdir -p /var/log/railmind && chown -R railmind:railmind /var/log/railmind /app

USER railmind

ENV PATH=/home/railmind/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
