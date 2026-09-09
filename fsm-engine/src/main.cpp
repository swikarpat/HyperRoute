#include <iostream>
#include <memory>
#include <string>
#include <csignal>
#include <thread>
#include <grpcpp/grpcpp.h>
#include "fsm_service_impl.hpp"
#include "rocksdb_storage.hpp"

int main([[maybe_unused]] int argc, [[maybe_unused]] char **argv)
{
    // Block SIGINT and SIGTERM so they can be handled synchronously by a dedicated thread
    sigset_t sigset;
    sigemptyset(&sigset);
    sigaddset(&sigset, SIGINT);
    sigaddset(&sigset, SIGTERM);
    pthread_sigmask(SIG_BLOCK, &sigset, nullptr);

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

        std::unique_ptr<grpc::Server> server = builder.BuildAndStart();
        std::cout << "==================================================" << std::endl;
        std::cout << "  ApexGateway C++20 FSM Compliance Engine Running  " << std::endl;
        std::cout << "  Endpoint: " << server_address << std::endl;
        std::cout << "  RocksDB:  " << rocksdb_path << std::endl;
        std::cout << "==================================================" << std::endl;

        // Dedicated thread waits for shutdown signals outside signal handler context
        std::thread signal_thread([&server, &sigset]() {
            int sig = 0;
            sigwait(&sigset, &sig);
            std::cout << "\n[Signal " << sig << "] Shutting down FSM Engine server gracefully..." << std::endl;
            server->Shutdown();
        });

        server->Wait();
        if (signal_thread.joinable())
        {
            signal_thread.join();
        }
    }
    catch (const std::exception &e)
    {
        std::cerr << "[Fatal Error] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "[Shutdown] Server stopped cleanly." << std::endl;
    return 0;
}
