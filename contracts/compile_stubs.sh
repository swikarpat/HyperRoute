#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GRPC_CPP_PLUGIN="$(which grpc_cpp_plugin || echo '/opt/homebrew/bin/grpc_cpp_plugin')"

cd "$SCRIPT_DIR"

FSM_DIR="$ROOT_DIR/fsm-engine"
AGENT_DIR="$ROOT_DIR/agent-runtime"

if [ -f "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [ -f "$AGENT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$AGENT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(which python3)"
fi

# Clean previous generated stubs
rm -rf "$FSM_DIR/generated/hyperroute"
rm -rf "$AGENT_DIR/generated/hyperroute"
mkdir -p "$FSM_DIR/generated"
mkdir -p "$AGENT_DIR/generated"

echo "==> Compiling C++20 Protobuf & gRPC stubs into: $FSM_DIR/generated"
protoc -I=proto \
  --cpp_out="$FSM_DIR/generated" \
  --grpc_out="$FSM_DIR/generated" \
  --plugin=protoc-gen-grpc="$GRPC_CPP_PLUGIN" \
  proto/hyperroute/v1/fsm_engine.proto

echo "==> Compiling Python Protobuf & gRPC stubs into: $AGENT_DIR/generated"
$PYTHON_BIN -m grpc_tools.protoc \
  -I=proto \
  --python_out="$AGENT_DIR/generated" \
  --grpc_python_out="$AGENT_DIR/generated" \
  proto/hyperroute/v1/fsm_engine.proto

# Create package markers for Python module imports
touch "$AGENT_DIR/generated/__init__.py"
mkdir -p "$AGENT_DIR/generated/hyperroute/v1"
touch "$AGENT_DIR/generated/hyperroute/__init__.py"
touch "$AGENT_DIR/generated/hyperroute/v1/__init__.py"

# Apply relative import patch for Python 3.14
for f in "$AGENT_DIR/generated/hyperroute/v1/fsm_engine_pb2_grpc.py" "$AGENT_DIR/src/proto/hyperroute/v1/fsm_engine_pb2_grpc.py"; do
  if [ -f "$f" ]; then
    sed -i '' -e 's/from hyperroute.v1 import fsm_engine_pb2 as/from . import fsm_engine_pb2 as/g' -e 's/import hyperroute.v1.fsm_engine_pb2 as/from . import fsm_engine_pb2 as/g' "$f" 2>/dev/null || \
    sed -i -e 's/from hyperroute.v1 import fsm_engine_pb2 as/from . import fsm_engine_pb2 as/g' -e 's/import hyperroute.v1.fsm_engine_pb2 as/from . import fsm_engine_pb2 as/g' "$f"
  fi
done

# Sync Python stubs to src/proto if used by FastAPI
if [ -d "$AGENT_DIR/src/proto" ]; then
  mkdir -p "$AGENT_DIR/src/proto/hyperroute/v1"
  cp -r "$AGENT_DIR/generated/hyperroute" "$AGENT_DIR/src/proto/"
fi

echo "✓ All stubs compiled cleanly under hyperroute.v1"
