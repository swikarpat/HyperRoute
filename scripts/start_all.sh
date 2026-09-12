#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

echo "=================================================================="
echo "          HYPERROUTE ENTERPRISE MESH STARTUP ORCHESTRATOR         "
echo "=================================================================="

# Helper to check if a port is in use
is_port_in_use() {
  lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
}

# 1. Start C++20 FSM Compliance Engine (:50051)
if is_port_in_use 50051; then
  echo "✓ Port 50051 is already active (FSM Engine is running)."
else
  FSM_BIN="$ROOT_DIR/fsm-engine/build/fsm_engine_server"
  if [ ! -f "$FSM_BIN" ]; then
    echo "==> Building C++20 FSM Engine..."
    cmake -B "$ROOT_DIR/fsm-engine/build" -S "$ROOT_DIR/fsm-engine"
    cmake --build "$ROOT_DIR/fsm-engine/build"
  fi
  echo "==> Starting C++20 FSM Engine on :50051..."
  "$FSM_BIN" > "$LOG_DIR/fsm_engine.log" 2>&1 &
  echo $! > "$PID_DIR/fsm_engine.pid"
  sleep 1
  echo "✓ C++20 FSM Engine started (PID: $(cat "$PID_DIR/fsm_engine.pid"))."
fi

# 2. Start Python 3.14 Agent Runtime (:8000)
if is_port_in_use 8000; then
  echo "✓ Port 8000 is already active (Agent Runtime is running)."
else
  echo "==> Starting Agent Runtime on :8000..."
  PYTHON_BIN="$ROOT_DIR/agent-runtime/.venv/bin/python"
  if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(which python3)"
  fi
  (cd "$ROOT_DIR" && PYTHONPATH="$ROOT_DIR/agent-runtime" "$PYTHON_BIN" -m uvicorn src.main:app --app-dir "$ROOT_DIR/agent-runtime" --host 0.0.0.0 --port 8000 > "$LOG_DIR/agent_runtime.log" 2>&1 & echo $! > "$PID_DIR/agent_runtime.pid")
  sleep 2
  echo "✓ Agent Runtime started (PID: $(cat "$PID_DIR/agent_runtime.pid"))."
fi

# 3. Start Spring Cloud Gateway (:8080)
if is_port_in_use 8080; then
  echo "✓ Port 8080 is already active (Gateway is running)."
else
  echo "==> Starting Spring Cloud Gateway on :8080..."
  (cd "$ROOT_DIR" && ./gateway/gradlew -p gateway bootRun --no-daemon > "$LOG_DIR/gateway.log" 2>&1 & echo $! > "$PID_DIR/gateway.pid")
  echo "✓ Gateway starting in background (PID: $(cat "$PID_DIR/gateway.pid"))..."
fi

# 4. Start React Frontend (:5173)
if is_port_in_use 5173; then
  echo "✓ Port 5173 is already active (Frontend is running)."
else
  echo "==> Starting Vite Frontend on :5173..."
  (cd "$ROOT_DIR/frontend" && npm run dev -- --host 0.0.0.0 --port 5173 > "$LOG_DIR/frontend.log" 2>&1 & echo $! > "$PID_DIR/frontend.pid")
  sleep 2
  echo "✓ Frontend started (PID: $(cat "$PID_DIR/frontend.pid"))."
fi

echo ""
echo "=================================================================="
echo "                  HYPERROUTE SERVICES ONLINE                      "
echo "=================================================================="
echo " • React Mission Control:  http://localhost:5173"
echo " • Reactive API Gateway:   http://localhost:8080"
echo " • Actuator & Health:      http://localhost:8080/actuator/health"
echo " • Agent Ingress Endpoint: http://localhost:8080/api/v1/gateway/alerts"
echo " • Python Agent Runtime:   http://localhost:8000/api/v1/agent/evaluate"
echo " • C++20 FSM Compliance:   127.0.0.1:50051 (gRPC)"
echo " Logs directory:           $LOG_DIR"
echo "=================================================================="

