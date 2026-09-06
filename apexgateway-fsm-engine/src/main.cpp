#include <iostream>
#include <memory>
#include <string>
#include <csignal>
#include <grpcpp/grpcpp.h>
#include "fsm_service_impl.hpp"
#include "rocksdb_storage.hpp"

std::unique_ptr<grpc::Server> g_server;

void handle_signal([[maybe_unused]] int signal)
{
    std::cout << "\n[Signal] Shutting down FSM Engine server gracefully..." << std::endl;
    if (g_server)
    {
        g_server->Shutdown();
    }
}

int main([[maybe_unused]] int argc, [[maybe_unused]] char **argv)
{
    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    const std::string server_address = "0.0.0.0:50051";
    const std::string rocksdb_path = "/tmp/apexgateway_rocksdb";

    try
    {
        apexgateway::storage::RocksStorageEngine storage(rocksdb_path);
        apexgateway::service::FsmComplianceServiceImpl service(storage);

        grpc::ServerBuilder builder;
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
        builder.RegisterService(&service);

        builder.SetMaxReceiveMessageSize(16 * 1024 * 1024);
        builder.SetMaxSendMessageSize(16 * 1024 * 1024);

        g_server = builder.BuildAndStart();
        std::cout << "==================================================" << std::endl;
        std::cout << "  ApexGateway C++20 FSM Compliance Engine Running  " << std::endl;
        std::cout << "  Endpoint: " << server_address << std::endl;
        std::cout << "  RocksDB:  " << rocksdb_path << std::endl;
        std::cout << "==================================================" << std::endl;

        g_server->Wait();
    }
    catch (const std::exception &e)
    {
        std::cerr << "[Fatal Error] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "[Shutdown] Server stopped cleanly." << std::endl;
    return 0;
}