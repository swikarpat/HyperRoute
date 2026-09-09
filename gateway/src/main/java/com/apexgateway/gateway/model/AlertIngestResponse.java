package com.apexgateway.gateway.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AlertIngestResponse(
    @JsonProperty("workflow_id") String workflowId,
    @JsonProperty("status") String status,
    @JsonProperty("final_fsm_state") int finalFsmState,
    @JsonProperty("total_steps_executed") int totalStepsExecuted,
    @JsonProperty("transaction_amount") double transactionAmount,
    @JsonProperty("gateway_latency_ms") long gatewayLatencyMs,
    @JsonProperty("circuit_breaker_status") String circuitBreakerStatus
) {}