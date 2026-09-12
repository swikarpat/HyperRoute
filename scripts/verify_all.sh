#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=================================================================="
echo "          HYPERROUTE FULL SYSTEM VERIFICATION SUITE               "
echo "=================================================================="

# 1. Python Unit & Multi-Agent Tests
echo ""
echo "==> [1/4] Running Python Agent & Security Test Suite..."
PYTHON_BIN="$ROOT_DIR/agent-runtime/.venv/bin/pytest"
if [ -x "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" tests/
else
  pytest tests/
fi
echo "✓ Python test suite passed cleanly."

# 2. C++20 FSM Engine Compilation
echo ""
echo "==> [2/4] Building C++20 FSM Compliance Engine..."
cmake -B "$ROOT_DIR/fsm-engine/build" -S "$ROOT_DIR/fsm-engine"
cmake --build "$ROOT_DIR/fsm-engine/build"
echo "✓ C++20 FSM Engine built successfully."

# 3. React Frontend Build & Typecheck
echo ""
echo "==> [3/4] Building React TypeScript Frontend..."
npm --prefix "$ROOT_DIR/frontend" run build
echo "✓ Frontend built successfully."

# 4. Java Gateway Integration Tests
echo ""
echo "==> [4/4] Running Spring Cloud Gateway Tests..."
./gradlew test
echo "✓ Gateway unit & integration tests passed."

echo ""
echo "=================================================================="
echo "  ✓ ALL HYPERROUTE SYSTEM-LEVEL VERIFICATION CHECKS PASSED (100%) "
echo "=================================================================="

