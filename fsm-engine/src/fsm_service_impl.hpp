#pragma once

#include <grpcpp/grpcpp.h>
#include "apexgateway/v1/fsm_engine.grpc.pb.h"
#include "fsm_engine.hpp"
#include "rocksdb_storage.hpp"
#include <unordered_map>
#include <mutex>
#include <chrono>

namespace apexgateway::service
{

    class FsmComplianceServiceImpl final : public v1::FsmComplianceEngine::Service
    {
    public:
        explicit FsmComplianceServiceImpl(storage::RocksStorageEngine &storage)
            : storage_(storage) {}

        grpc::Status ValidateTransition(
            [[maybe_unused]] grpc::ServerContext *context,
            const v1::StateTransitionRequest *request,
            v1::StateTransitionResponse *response) override
        {
            const auto start_time = std::chrono::steady_clock::now();

            core::WorkflowStateSlot *slot = get_or_create_slot(request->workflow_id());

            uint32_t rejection_code = 0;
            std::string rejection_reason;

            bool allowed = fsm_.validate_transition(
                *slot,
                static_cast<uint32_t>(request->to_state()),
                rejection_code,
                rejection_reason);

            response->set_is_allowed(allowed);
            response->set_rejection_code(rejection_code);
            response->set_rejection_reason(rejection_reason);
            response->set_current_state(static_cast<v1::AgentState>(slot->current_state.load()));

            if (allowed)
            {
                storage_.record_history(
                    request->workflow_id(),
                    request->step_index(),
                    "State=" + std::to_string(static_cast<int>(request->to_state())));
            }

            const auto end_time = std::chrono::steady_clock::now();
            const auto latency_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();
            response->set_step_latency_ns(latency_ns);

            *response->mutable_trace_context() = request->trace_context();
            return grpc::Status::OK;
        }

        grpc::Status InspectTokenStream(
            [[maybe_unused]] grpc::ServerContext *context,
            grpc::ServerReaderWriter<v1::TokenInspectionResult, v1::TokenInspectionChunk> *stream) override
        {
            v1::TokenInspectionChunk chunk;
            while (stream->Read(&chunk))
            {
                const auto start_time = std::chrono::steady_clock::now();

                uint32_t mask = fsm_.scan_token_chunk(chunk.token_text());

                v1::TokenInspectionResult result;
                result.set_is_clean(mask == 0);
                result.set_violation_mask(mask);
                result.set_sanitized_text(mask == 0 ? chunk.token_text() : "[REDACTED_BY_GUARDRAIL]");

                const auto end_time = std::chrono::steady_clock::now();
                result.set_scan_duration_ns(
                    std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count());

                stream->Write(result);
            }
            return grpc::Status::OK;
        }

        grpc::Status RecoverWorkflow(
            [[maybe_unused]] grpc::ServerContext *context,
            const v1::StateTransitionRequest *request,
            v1::WorkflowSnapshot *response) override
        {
            response->set_workflow_id(request->workflow_id());
            response->set_agent_id(request->agent_id());

            std::lock_guard<std::mutex> lock(slots_mutex_);
            auto it = active_slots_.find(request->workflow_id());
            if (it != active_slots_.end())
            {
                response->set_current_state(static_cast<v1::AgentState>(it->second.current_state.load()));
                response->set_total_steps(it->second.execution_step.load());
            }
            else
            {
                response->set_current_state(v1::AGENT_STATE_IDLE);
                response->set_total_steps(0);
            }

            auto history = storage_.get_history(request->workflow_id());
            response->set_memory_footprint_bytes(sizeof(core::WorkflowStateSlot) + (history.size() * 32));
            response->set_is_locked(false);
            return grpc::Status::OK;
        }

    private:
        core::DeterministicFsmEngine fsm_;
        storage::RocksStorageEngine &storage_;
        std::mutex slots_mutex_;
        std::unordered_map<std::string, core::WorkflowStateSlot> active_slots_;

        core::WorkflowStateSlot *get_or_create_slot(const std::string &workflow_id)
        {
            std::lock_guard<std::mutex> lock(slots_mutex_);
            auto it = active_slots_.find(workflow_id);
            if (it == active_slots_.end())
            {
                auto &slot = active_slots_[workflow_id];
                slot.reset(1, 0);
                return &slot;
            }
            return &it->second;
        }
    };

} // namespace apexgateway::service