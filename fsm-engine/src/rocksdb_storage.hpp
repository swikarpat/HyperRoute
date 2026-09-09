#pragma once

#include <rocksdb/db.h>
#include <string>
#include <vector>
#include <memory>

namespace apexgateway::storage
{

    class RocksStorageEngine
    {
    public:
        explicit RocksStorageEngine(const std::string &db_path);
        ~RocksStorageEngine();

        void put_scratchpad(const std::string &key, const std::string &value);
        bool get_scratchpad(const std::string &key, std::string &value);

        void record_history(const std::string &workflow_id, uint64_t step, const std::string &record);
        std::vector<std::string> get_history(const std::string &workflow_id);

    private:
        std::unique_ptr<rocksdb::DB> db_;
        std::vector<rocksdb::ColumnFamilyHandle *> handles_;
    };

} // namespace apexgateway::storage