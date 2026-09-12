# Multi-stage C++20 FSM Compliance Engine Dockerfile
# Stage 1: Build & Compilation
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    libgrpc++-dev \
    protobuf-compiler-grpc \
    librocksdb-dev \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    liblz4-dev \
    libzstd-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . .

RUN mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . --parallel $(nproc)

# Stage 2: Ultra-Minimal Hardened Runtime
FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libprotobuf32t64 \
    libgrpc++1.51 \
    librocksdb8.10 \
    libsnappy1v5 \
    zlib1g \
    libbz2-1.0 \
    liblz4-1 \
    libzstd1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 10001 -m -s /bin/bash hyperroute

WORKDIR /app
COPY --from=builder /workspace/build/fsm_engine_server /app/fsm_engine_server

# Permissions & state scratchpad directory
RUN mkdir -p /tmp/hyperroute_rocksdb && chown -R hyperroute:hyperroute /app /tmp/hyperroute_rocksdb

USER hyperroute
EXPOSE 50051

ENTRYPOINT ["/app/fsm_engine_server"]

