#!/usr/bin/env bash
# ==============================================================================
# HyperRoute Local AWS Services & Infrastructure Validation Script
# Simulates AWS Secrets Manager, SQS DLQ, SNS Fan-Out, and S3 OAC with zero AWS spend.
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================================="
echo " Starting HyperRoute Local AWS Architecture Validation (\$0.00 Spend) "
echo "=================================================================="

# 1. Check Python Virtual Environment
if [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

# 2. Run AWS Services Moto Simulation
$PYTHON_BIN scripts/test_aws_simulation.py

# 3. Validate Kubernetes Production Manifests
echo "==> [K8s Test] Validating Kubernetes Kustomize manifests..."
kubectl kustomize deploy/k8s/ > /dev/null
echo "  ✔ Kubernetes production manifests rendered cleanly."

# 4. Validate Terraform IaC
echo "==> [IaC Test] Validating Terraform configuration syntax..."
cd infrastructure/terraform
TF_CLI_CONFIG_FILE=/dev/null terraform fmt -check > /dev/null
echo "  ✔ Terraform files formatted according to HashiCorp standards."

echo ""
echo "=================================================================="
echo "  HyperRoute AWS Local Stack Verification Complete & Passed!      "
echo "=================================================================="
