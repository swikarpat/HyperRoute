#include "rocksdb_storage.hpp"
#include <rocksdb/options.h>
#include <rocksdb/table.h>
#include <stdexcept>
#include <iostream>

namespace hyperroute::storage
{

    RocksStorageEngine::RocksStorageEngine(const std::string &db_path)
    {
        rocksdb::DBOptions db_options;
        db_options.create_if_missing = true;
        db_options.create_missing_column_families = true;
        db_options.max_background_jobs = 4;

        auto table_options = std::make_shared<rocksdb::BlockBasedTableOptions>();
        table_options->block_size = 16 * 1024;
        table_options->cache_index_and_filter_blocks = true;

        rocksdb::ColumnFamilyOptions default_cf;
        default_cf.table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));

        rocksdb::ColumnFamilyOptions scratchpad_cf;
        scratchpad_cf.table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));
        scratchpad_cf.compression = rocksdb::kLZ4Compression;

        rocksdb::ColumnFamilyOptions history_cf;
        history_cf.table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));
        history_cf.compression = rocksdb::kZSTD;

        rocksdb::ColumnFamilyOptions violations_cf;
        violations_cf.table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));

        std::vector<rocksdb::ColumnFamilyDescriptor> column_families = {
            {rocksdb::kDefaultColumnFamilyName, default_cf},
            {"cf_agent_scratchpad", scratchpad_cf},
            {"cf_fsm_history", history_cf},
            {"cf_guardrail_violations", violations_cf}};

        rocksdb::Status status = rocksdb::DB::Open(db_options, db_path, column_families, &handles_, &db_);
        if (!status.ok())
        {
            throw std::runtime_error("Failed to initialize RocksDB at " + db_path + ": " + status.ToString());
        }
        std::cout << "[RocksDB] Storage engine initialized with 4 Column Families at: " << db_path << std::endl;
    }

    RocksStorageEngine::~RocksStorageEngine()
    {
        for (auto *handle : handles_)
        {
            if (handle && db_)
            {
                db_->DestroyColumnFamilyHandle(handle);
            }
        }
    }

    void RocksStorageEngine::put_scratchpad(const std::string &key, const std::string &value)
    {
        rocksdb::WriteOptions write_options;
        write_options.sync = false;
        db_->Put(write_options, handles_[1], key, value);
    }

    bool RocksStorageEngine::get_scratchpad(const std::string &key, std::string &value)
    {
        rocksdb::ReadOptions read_options;
        rocksdb::Status s = db_->Get(read_options, handles_[1], key, &value);
        return s.ok();
    }

    void RocksStorageEngine::record_history(const std::string &workflow_id, uint64_t step, const std::string &record)
    {
        rocksdb::WriteOptions write_options;
        std::string key = workflow_id + "#" + std::to_string(step);
        db_->Put(write_options, handles_[2], key, record);
    }

    std::vector<std::string> RocksStorageEngine::get_history(const std::string &workflow_id)
    {
        std::vector<std::string> results;
        rocksdb::ReadOptions read_options;
        std::unique_ptr<rocksdb::Iterator> it(db_->NewIterator(read_options, handles_[2]));

        std::string prefix = workflow_id + "#";
        for (it->Seek(prefix); it->Valid() && it->key().starts_with(prefix); it->Next())
        {
            results.push_back(it->value().ToString());
        }
        return results;
    }

} // namespace hyperroute::storage
