# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create a non-privileged user and setup log dir
RUN useradd -m -s /bin/bash railmind && \
    mkdir -p /var/log/railmind && \
    chown -R railmind:railmind /var/log/railmind

WORKDIR /app

# Copy python dependencies from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Change ownership of app code
RUN chown -R railmind:railmind /app

# Run as non-privileged user
USER railmind

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
