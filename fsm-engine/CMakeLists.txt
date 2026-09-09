cmake_minimum_required(VERSION 3.24)
project(apexgateway_fsm_engine CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Optimization flags for Apple Silicon
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Wextra -pthread")

set(HOMEBREW_PREFIX "/opt/homebrew")

# Enforce CONFIG mode to prevent FindProtobuf target collision with gRPC
find_package(Protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Locate RocksDB from Homebrew
find_library(ROCKSDB_LIBRARY rocksdb HINTS "${HOMEBREW_PREFIX}/lib" REQUIRED)

include_directories(
    ${HOMEBREW_PREFIX}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/generated
)

set(PROTO_SRCS
    generated/apexgateway/v1/fsm_engine.pb.cc
    generated/apexgateway/v1/fsm_engine.grpc.pb.cc
)

add_executable(fsm_engine_server
    src/main.cpp
    src/rocksdb_storage.cpp
    ${PROTO_SRCS}
)

target_link_libraries(fsm_engine_server PRIVATE
    ${ROCKSDB_LIBRARY}
    gRPC::grpc++
    protobuf::libprotobuf
    Threads::Threads
)