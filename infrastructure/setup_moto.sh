#!/usr/bin/env bash
set -e

# 1. Stop and purge any existing failing containers
docker stop apex-aws-local 2>/dev/null || true
docker rm apex-aws-local 2>/dev/null || true

# 2. Write the verified production docker-compose
cat <<'COMPOSE_EOF' > docker-compose.yml
services:
  kafka:
    image: bitnami/kafka:latest
    container_name: apex-kafka
    ports:
      - "9092:9092"
    environment:
      - KAFKA_CFG_NODE_ID=0
      - KAFKA_CFG_PROCESS_ROLES=controller,broker
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093
      - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
    restart: unless-stopped

  redis:
    image: redis/redis-stack-server:latest
    container_name: apex-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: apex-jaeger
    ports:
      - "16686:16686"
      - "4317"
    restart: unless-stopped

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: apex-otel
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"
      - "4318:4318"
    depends_on:
      - jaeger
    restart: unless-stopped

  aws-mock:
    image: motoserver/moto:latest
    container_name: apex-aws-local
    ports:
      - "4566:5000"
    restart: unless-stopped
COMPOSE_EOF

# 3. Spin up Moto
docker compose up -d aws-mock

# 4. Wait for Moto port 4566
echo "Waiting for local AWS mock server..."
until curl -s http://localhost:4566/ > /dev/null 2>&1; do
  sleep 1
done
echo "✓ Local AWS mock server is online on port 4566!"

# 5. Provision Mock AWS Infrastructure
export AWS_ACCESS_KEY_ID="mock-key-test"
export AWS_SECRET_ACCESS_KEY="mock-secret-test"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ENDPOINT="http://localhost:4566"

echo "==> Creating S3 Audit Bucket..."
aws --endpoint-url="$AWS_ENDPOINT" s3 mb s3://apexgateway-audit-ledger

echo "==> Creating Secrets Manager Secret..."
aws --endpoint-url="$AWS_ENDPOINT" secretsmanager create-secret \
  --name "apexgateway/fsm-compliance-keys" \
  --description "HMAC Signing keys for state transitions" \
  --secret-string '{"signing_key":"apex-enterprise-sec-9901","simd_salt":"simd-avx512-salt"}'

echo "==> Verifying Mock S3 Buckets:"
aws --endpoint-url="$AWS_ENDPOINT" s3 ls

echo "==> Verifying Mock Secrets Manager:"
aws --endpoint-url="$AWS_ENDPOINT" secretsmanager describe-secret \
  --secret-id "apexgateway/fsm-compliance-keys"
