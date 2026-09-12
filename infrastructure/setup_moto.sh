#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Starting AWS Moto Mock server from docker-compose..."
docker compose up -d moto

echo "==> Waiting for Moto server to respond on port 4566..."
MAX_RETRIES=30
RETRY=0
until curl -s http://localhost:4566/ > /dev/null 2>&1 || [ $RETRY -eq $MAX_RETRIES ]; do
  sleep 1
  RETRY=$((RETRY+1))
done

if [ $RETRY -eq $MAX_RETRIES ]; then
  echo "⚠️ Warning: Moto did not respond within 30s. Check docker logs."
  exit 1
fi

echo "✓ Local AWS Moto server is online on port 4566!"

# Provision Mock AWS Infrastructure for HyperRoute
export AWS_ACCESS_KEY_ID="mock-key-test"
export AWS_SECRET_ACCESS_KEY="mock-secret-test"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ENDPOINT="http://localhost:4566"

if command -v aws >/dev/null 2>&1; then
  echo "==> Creating S3 Audit Bucket: s3://hyperroute-audit-ledger..."
  aws --endpoint-url="$AWS_ENDPOINT" s3 mb s3://hyperroute-audit-ledger 2>/dev/null || true

  echo "==> Creating Secrets Manager Secret: hyperroute/fsm-compliance-keys..."
  aws --endpoint-url="$AWS_ENDPOINT" secretsmanager create-secret \
    --name "hyperroute/fsm-compliance-keys" \
    --description "HMAC Signing keys for state transitions" \
    --secret-string '{"signing_key":"hyperroute-enterprise-sec-9901","simd_salt":"simd-avx512-salt"}' 2>/dev/null || \
  aws --endpoint-url="$AWS_ENDPOINT" secretsmanager put-secret-value \
    --secret-id "hyperroute/fsm-compliance-keys" \
    --secret-string '{"signing_key":"hyperroute-enterprise-sec-9901","simd_salt":"simd-avx512-salt"}'

  echo "✓ S3 Buckets:"
  aws --endpoint-url="$AWS_ENDPOINT" s3 ls
  echo "✓ Secrets Manager:"
  aws --endpoint-url="$AWS_ENDPOINT" secretsmanager describe-secret --secret-id "hyperroute/fsm-compliance-keys"
else
  echo "ℹ️ AWS CLI not found on host. Moto mock endpoint is available at http://localhost:4566."
fi
