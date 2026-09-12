#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.pids"

echo "==> Stopping HyperRoute services..."

stop_pid() {
  local service_name="$1"
  local pid_file="$PID_DIR/${service_name}.pid"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $service_name (PID: $pid)..."
      kill "$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pid_file"
  fi
}

stop_pid "frontend"
stop_pid "gateway"
stop_pid "agent_runtime"
stop_pid "fsm_engine"

# Also clean any processes on dedicated ports if lingering
kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null)"
  if [ -n "$pids" ]; then
    echo "Clearing lingering process on port $port (PIDs: $pids)..."
    kill $pids 2>/dev/null || true
  fi
}

kill_port 5173
kill_port 8080
kill_port 8000
kill_port 50051

echo "✓ All HyperRoute services stopped."

