.PHONY: help build test stubs dev-infra start stop verify clean aws-test tf-validate k8s-validate docker-build

help:
	@echo "HyperRoute Developer & Automation CLI"
	@echo "  make build        - Build C++ FSM, Java Gateway, and Frontend"
	@echo "  make test         - Run all test suites across tiers"
	@echo "  make aws-test     - Validate enterprise AWS services locally with \$$0.00 spend"
	@echo "  make tf-validate  - Validate Terraform IaC configuration"
	@echo "  make k8s-validate - Validate Kubernetes Kustomize manifests"
	@echo "  make docker-build - Build local Docker containers for all tiers"
	@echo "  make stubs        - Compile gRPC and Protobuf contracts"
	@echo "  make dev-infra    - Start Redis, Moto, and Observability stack"
	@echo "  make start        - Launch all HyperRoute runtime services in background"
	@echo "  make stop         - Terminate all running HyperRoute processes"
	@echo "  make verify       - Execute full automated verification pipeline"
	@echo "  make clean        - Clean all build outputs and logs"

stubs:
	@bash contracts/generate_stubs.sh

build: stubs
	@echo "==> Building C++ FSM Engine..."
	@cmake -B fsm-engine/build -S fsm-engine
	@cmake --build fsm-engine/build
	@echo "==> Building Java Gateway..."
	@./gradlew build -x test
	@echo "==> Building React Frontend..."
	@npm --prefix frontend run build

test:
	@echo "==> Running Python tests..."
	@./.venv/bin/pytest tests/
	@echo "==> Running Java Gateway tests..."
	@./gradlew :gateway:test

aws-test:
	@bash scripts/test_aws_local.sh

tf-validate:
	@echo "==> Checking Terraform formatting..."
	@cd infrastructure/terraform && TF_CLI_CONFIG_FILE=/dev/null terraform fmt -check
	@echo "==> Validating Terraform syntax..."
	@cd infrastructure/terraform && TF_CLI_CONFIG_FILE=/dev/null terraform validate

k8s-validate:
	@echo "==> Validating Kubernetes Kustomize manifests..."
	@kubectl kustomize deploy/k8s/ > /dev/null
	@echo "  ✔ Kubernetes manifests valid."

docker-build:
	@echo "==> Building Docker images..."
	@docker build -f agent-runtime/Dockerfile -t hyperroute-agent-runtime:latest .
	@docker build -f frontend/Dockerfile -t hyperroute-frontend:latest frontend/
	@docker build -f gateway/Dockerfile -t hyperroute-gateway:latest gateway/
	@docker build -f fsm-engine/Dockerfile -t hyperroute-fsm-engine:latest fsm-engine/

dev-infra:
	@echo "==> Starting Docker development infrastructure..."
	@docker compose -f infrastructure/docker-compose.yml up -d redis moto tempo loki prometheus grafana otel-collector

start:
	@bash scripts/start_all.sh

stop:
	@bash scripts/stop_all.sh

verify:
	@bash scripts/verify_all.sh

clean:
	@./gradlew clean
	@rm -rf fsm-engine/build/CMakeFiles fsm-engine/build/CMakeCache.txt fsm-engine/build/fsm_engine_server
	@rm -rf frontend/dist .pids .logs
