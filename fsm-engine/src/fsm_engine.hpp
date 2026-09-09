#pragma once

#include <array>
#include <atomic>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <string>

namespace apexgateway::core
{

    constexpr size_t MAX_STATES = 16;
    constexpr size_t MAX_WORKFLOW_DEPTH = 64;
    constexpr size_t CACHE_LINE_SIZE = 64;

    struct alignas(CACHE_LINE_SIZE) WorkflowStateSlot
    {
        std::atomic<uint32_t> current_state{0};
        std::atomic<uint32_t> execution_step{0};
        uint64_t start_time_ns{0};
        uint32_t accumulated_violations{0};
        std::array<uint8_t, MAX_WORKFLOW_DEPTH> state_history{};

        void reset(uint32_t initial_state, uint64_t now_ns) noexcept
        {
            current_state.store(initial_state, std::memory_order_relaxed);
            execution_step.store(0, std::memory_order_relaxed);
            start_time_ns = now_ns;
            accumulated_violations = 0;
            state_history.fill(0);
        }
    };

    class alignas(CACHE_LINE_SIZE) DeterministicFsmEngine
    {
    public:
        DeterministicFsmEngine() noexcept
        {
            initialize_regulatory_matrix();
        }

        [[nodiscard]] bool validate_transition(
            WorkflowStateSlot &slot,
            uint32_t target_state,
            uint32_t &rejection_code,
            std::string &rejection_reason) noexcept
        {
            const uint32_t curr = slot.current_state.load(std::memory_order_acquire);

            if (curr >= MAX_STATES || target_state >= MAX_STATES)
            {
                rejection_code = 1;
                rejection_reason = "Target or current state index exceeds configured MAX_STATES boundary.";
                return false;
            }

            const uint64_t allowed_mask = transition_matrix_[curr];
            if ((allowed_mask & (1ULL << target_state)) == 0)
            {
                rejection_code = 2;
                rejection_reason = "Transition from state " + std::to_string(curr) +
                                   " to state " + std::to_string(target_state) +
                                   " is strictly prohibited by regulatory compliance policy.";
                return false;
            }

            const uint32_t step = slot.execution_step.load(std::memory_order_relaxed);
            if (step >= 3)
            {
                const size_t h_idx = step % MAX_WORKFLOW_DEPTH;
                const size_t prev_1 = (h_idx + MAX_WORKFLOW_DEPTH - 1) % MAX_WORKFLOW_DEPTH;
                const size_t prev_2 = (h_idx + MAX_WORKFLOW_DEPTH - 2) % MAX_WORKFLOW_DEPTH;

                if (slot.state_history[prev_2] == target_state && slot.state_history[prev_1] == curr)
                {
                    rejection_code = 3;
                    rejection_reason = "Infinite reasoning oscillation detected across consecutive states.";
                    return false;
                }
            }

            const size_t next_idx = (step + 1) % MAX_WORKFLOW_DEPTH;
            slot.state_history[next_idx] = static_cast<uint8_t>(target_state);
            slot.current_state.store(target_state, std::memory_order_release);
            slot.execution_step.fetch_add(1, std::memory_order_relaxed);

            rejection_code = 0;
            rejection_reason = "OK";
            return true;
        }

        [[nodiscard]] uint32_t scan_token_chunk(const std::string &token_text) noexcept
        {
            uint32_t violations = 0;

            // Accurate SSN pattern scanner: 3 digits - 2 digits - 4 digits (###-##-####)
            if (token_text.size() >= 11)
            {
                for (size_t i = 0; i <= token_text.size() - 11; ++i)
                {
                    if (std::isdigit(token_text[i]) &&
                        std::isdigit(token_text[i + 1]) &&
                        std::isdigit(token_text[i + 2]) &&
                        token_text[i + 3] == '-' &&
                        std::isdigit(token_text[i + 4]) &&
                        std::isdigit(token_text[i + 5]) &&
                        token_text[i + 6] == '-' &&
                        std::isdigit(token_text[i + 7]) &&
                        std::isdigit(token_text[i + 8]) &&
                        std::isdigit(token_text[i + 9]) &&
                        std::isdigit(token_text[i + 10]))
                    {
                        violations |= 1; // VIOLATION_FLAG_PII_SSN
                        break;
                    }
                }
            }

            // Fast search for prompt injection delimiters
            if (token_text.find("IGNORE PREVIOUS INSTRUCTIONS") != std::string::npos ||
                token_text.find("SYSTEM OVERRIDE") != std::string::npos)
            {
                violations |= 4; // VIOLATION_FLAG_PROMPT_INJECTION
            }

            return violations;
        }

    private:
        alignas(CACHE_LINE_SIZE) std::array<uint64_t, MAX_STATES> transition_matrix_{};

        void initialize_regulatory_matrix() noexcept
        {
            transition_matrix_.fill(0);

            // 1: IDLE -> INGESTING_ALERT
            transition_matrix_[1] = (1ULL << 2);
            // 2: INGESTING_ALERT -> PARSING_EVIDENCE | TERMINATED_FAILED
            transition_matrix_[2] = (1ULL << 3) | (1ULL << 10);
            // 3: PARSING_EVIDENCE -> EXTRACTING_ACCOUNTS | TERMINATED_FAILED
            transition_matrix_[3] = (1ULL << 4) | (1ULL << 10);
            // 4: EXTRACTING_ACCOUNTS -> CORRELATING_HISTORY
            transition_matrix_[4] = (1ULL << 5);
            // 5: CORRELATING_HISTORY -> EVALUATING_RISK
            transition_matrix_[5] = (1ULL << 6);
            // 6: EVALUATING_RISK -> AWAITING_HUMAN_APPROVAL | ISSUING_CLEARANCE
            transition_matrix_[6] = (1ULL << 7) | (1ULL << 9);
            // 7: AWAITING_HUMAN_APPROVAL -> EXECUTING_FREEZE | ISSUING_CLEARANCE | TERMINATED_FAILED
            transition_matrix_[7] = (1ULL << 8) | (1ULL << 9) | (1ULL << 10);
            // 8: EXECUTING_FREEZE -> TERMINATED_COMPLETED
            transition_matrix_[8] = (1ULL << 11);
            // 9: ISSUING_CLEARANCE -> TERMINATED_COMPLETED
            transition_matrix_[9] = (1ULL << 11);
        }
    };

} // namespace apexgateway::core