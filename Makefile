.PHONY: help build test stubs dev-infra start stop verify clean

help:
	@echo "HyperRoute Developer & Automation CLI"
	@echo "  make build      - Build C++ FSM, Java Gateway, and Frontend"
	@echo "  make test       - Run all test suites across tiers"
	@echo "  make stubs      - Compile gRPC and Protobuf contracts"
	@echo "  make dev-infra  - Start Redis, Moto, and Observability stack"
	@echo "  make start      - Launch all HyperRoute runtime services in background"
	@echo "  make stop       - Terminate all running HyperRoute processes"
	@echo "  make verify     - Execute full automated verification pipeline"
	@echo "  make clean      - Clean all build outputs and logs"

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
	@./agent-runtime/.venv/bin/pytest tests/
	@echo "==> Running Java Gateway tests..."
	@./gradlew test

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

