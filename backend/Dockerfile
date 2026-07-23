# Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final Stage
FROM python:3.11-slim

# Create non-privileged user
RUN useradd -m -s /bin/bash railmind

WORKDIR /app

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Set ownership and create log dir
RUN mkdir -p /var/log/railmind && chown -R railmind:railmind /app /var/log/railmind

# Switch to non-privileged user
USER railmind

# Copy the rest of the application code
COPY --chown=railmind:railmind . /app/backend

# Expose API port
EXPOSE 8000

# Set Python Path
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
