# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM python:3.11-slim

# Create a non-privileged user
RUN useradd -m -s /bin/bash railmind

WORKDIR /home/railmind/app

# Copy python dependencies from builder
COPY --from=builder /root/.local /home/railmind/.local
ENV PATH=/home/railmind/.local/bin:$PATH

# Copy application code
COPY . .

# Change ownership
RUN chown -R railmind:railmind /home/railmind/app

# Switch to non-privileged user
USER railmind

EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
