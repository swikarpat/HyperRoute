# Multi-stage Dockerfile for HyperRoute Python Agent Runtime
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final minimal production container
FROM python:3.12-slim AS runtime

RUN useradd -u 10001 -m -s /bin/bash hyperroute

WORKDIR /app

COPY --from=builder /root/.local /home/hyperroute/.local
COPY --chown=hyperroute:hyperroute . /app

ENV PATH=/home/hyperroute/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER hyperroute
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

