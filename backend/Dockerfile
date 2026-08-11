FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim as runtime

# Create non-privileged user
RUN useradd -m -U -s /bin/bash railmind

WORKDIR /app
COPY --from=builder /root/.local /home/railmind/.local

COPY . .

RUN chown -R railmind:railmind /app

# Ensure logging directory exists and is accessible
RUN mkdir -p /var/log/railmind && chown -R railmind:railmind /var/log/railmind

USER railmind
ENV PATH=/home/railmind/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
