cmake_minimum_required(VERSION 3.24)
project(hyperroute_fsm_engine CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Wextra -pthread")

set(HOMEBREW_PREFIX "/opt/homebrew")

find_package(Protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)
find_package(Threads REQUIRED)

find_library(ROCKSDB_LIBRARY rocksdb HINTS "${HOMEBREW_PREFIX}/lib" REQUIRED)

include_directories(
    ${HOMEBREW_PREFIX}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/generated
)

set(PROTO_SRCS
    generated/hyperroute/v1/fsm_engine.pb.cc
    generated/hyperroute/v1/fsm_engine.grpc.pb.cc
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
