# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Create a non-privileged user
RUN useradd -m -r railmind

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/railmind/.local

# Copy application code
COPY . /app

# Create log directory with correct permissions
RUN mkdir -p /var/log/railmind && chown -R railmind:railmind /var/log/railmind

# Ensure path includes the local bin directory for the user
ENV PATH=/home/railmind/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to the non-privileged user
USER railmind

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
