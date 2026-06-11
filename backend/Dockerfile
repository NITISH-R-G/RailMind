# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app
COPY backend/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc &&     pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim

RUN useradd -m -r railmind

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/railmind/.local

# Add .local to PATH
ENV PATH=/home/railmind/.local/bin:$PATH

COPY . /app

# Set ownership
RUN chown -R railmind:railmind /app

USER railmind

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
