#!/usr/bin/env bash
set -e

ROOT_DIR=".."
GRPC_CPP_PLUGIN="$(which grpc_cpp_plugin)"

mkdir -p $ROOT_DIR/apexgateway-fsm-engine/generated
mkdir -p $ROOT_DIR/apexgateway-agent-runtime/generated

echo "==> Compiling C++20 Protobuf & gRPC stubs..."
protoc -I=proto \
  --cpp_out=$ROOT_DIR/apexgateway-fsm-engine/generated \
  --grpc_out=$ROOT_DIR/apexgateway-fsm-engine/generated \
  --plugin=protoc-gen-grpc="$GRPC_CPP_PLUGIN" \
  apexgateway/v1/fsm_engine.proto

echo "==> Compiling Python Protobuf & gRPC stubs..."
$ROOT_DIR/apexgateway-agent-runtime/.venv/bin/python -m grpc_tools.protoc \
  -I=proto \
  --python_out=$ROOT_DIR/apexgateway-agent-runtime/generated \
  --grpc_python_out=$ROOT_DIR/apexgateway-agent-runtime/generated \
  apexgateway/v1/fsm_engine.proto

# Create package markers for Python module imports
touch $ROOT_DIR/apexgateway-agent-runtime/generated/__init__.py
touch $ROOT_DIR/apexgateway-agent-runtime/generated/apexgateway/__init__.py
touch $ROOT_DIR/apexgateway-agent-runtime/generated/apexgateway/v1/__init__.py

echo "✓ All stubs compiled cleanly."
