#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=================================================================="
echo "          HYPERROUTE FULL SYSTEM VERIFICATION SUITE               "
echo "=================================================================="

# 1. Python Unit & Multi-Agent Tests
echo ""
echo "==> [1/5] Running Python Agent & Security Test Suite..."
if [ -x "$ROOT_DIR/.venv/bin/pytest" ]; then
  "$ROOT_DIR/.venv/bin/pytest" tests/
elif [ -x "$ROOT_DIR/agent-runtime/.venv/bin/pytest" ]; then
  "$ROOT_DIR/agent-runtime/.venv/bin/pytest" tests/
else
  pytest tests/
fi
echo "✓ Python test suite passed cleanly."

# 2. C++20 FSM Engine Compilation
echo ""
echo "==> [2/5] Building C++20 FSM Compliance Engine..."
cmake -B "$ROOT_DIR/fsm-engine/build" -S "$ROOT_DIR/fsm-engine"
cmake --build "$ROOT_DIR/fsm-engine/build"
echo "✓ C++20 FSM Engine built successfully."

# 3. React Frontend Build & Typecheck
echo ""
echo "==> [3/5] Building React TypeScript Frontend..."
npm --prefix "$ROOT_DIR/frontend" run build
echo "✓ Frontend built successfully."

# 4. Java Gateway & Banking Core Integration Tests
echo ""
echo "==> [4/5] Running Spring Cloud Gateway & Banking Core Tests..."
./gradlew test --no-daemon
echo "✓ Gateway and Banking Core unit & integration tests passed."

# 5. Local AWS Cloud Services & Infrastructure Verification ($0.00 spend)
echo ""
echo "==> [5/5] Validating AWS Enterprise Cloud Services & IaC..."
bash "$ROOT_DIR/scripts/test_aws_local.sh"
echo "✓ AWS local verification suite passed."

echo ""
echo "=================================================================="
echo "  ✓ ALL HYPERROUTE SYSTEM-LEVEL VERIFICATION CHECKS PASSED (100%) "
echo "=================================================================="
