#!/usr/bin/env bash
set -e

ROOT_DIR=".."
GRPC_CPP_PLUGIN="$(which grpc_cpp_plugin || echo '/opt/homebrew/bin/grpc_cpp_plugin')"

# Detect C++ and Python destination directories
FSM_DIR="$ROOT_DIR/fsm-engine"
[ ! -d "$FSM_DIR" ] && FSM_DIR="$ROOT_DIR/apexgateway-fsm-engine"

AGENT_DIR="$ROOT_DIR/agent-runtime"
[ ! -d "$AGENT_DIR" ] && AGENT_DIR="$ROOT_DIR/apexgateway-agent-runtime"

PYTHON_BIN="$AGENT_DIR/.venv/bin/python"
[ ! -f "$PYTHON_BIN" ] && PYTHON_BIN="$(which python3)"

# Clean previous generated stubs
rm -rf "$FSM_DIR/generated/hyperroute" "$FSM_DIR/generated/apexgateway"
rm -rf "$AGENT_DIR/generated/hyperroute" "$AGENT_DIR/generated/apexgateway"
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
