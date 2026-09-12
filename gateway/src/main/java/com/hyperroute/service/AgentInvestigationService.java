package com.hyperroute.service;

import com.hyperroute.model.AlertIngestRequest;
import com.hyperroute.model.AlertIngestResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.circuitbreaker.ReactiveCircuitBreaker;
import org.springframework.cloud.client.circuitbreaker.ReactiveCircuitBreakerFactory;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

@Service
public class AgentInvestigationService {

    private static final Logger log = LoggerFactory.getLogger(AgentInvestigationService.class);
    private final WebClient webClient;
    private final ReactiveCircuitBreakerFactory<?, ?> circuitBreakerFactory;

    public AgentInvestigationService(
            WebClient.Builder webClientBuilder,
            @Value("${hyperroute.agent-runtime-url:http://localhost:8000}") String agentRuntimeUrl,
            @Autowired(required = false) ReactiveCircuitBreakerFactory<?, ?> circuitBreakerFactory) {
        this.webClient = webClientBuilder
                .baseUrl(agentRuntimeUrl)
                .build();
        this.circuitBreakerFactory = circuitBreakerFactory;
    }

    public Mono<AlertIngestResponse> dispatchInvestigation(AlertIngestRequest request, long startTime) {
        Mono<AlertIngestResponse> call = webClient.post()
                .uri("/api/v1/agent/evaluate")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .timeout(Duration.ofSeconds(10))
                .map(responseMap -> {
                    String status = String.valueOf(responseMap.getOrDefault("status", "INVESTIGATED"));
                    int finalState = responseMap.get("final_fsm_state") instanceof Number num
                            ? num.intValue()
                            : 9;
                    int totalSteps = responseMap.get("total_steps_executed") instanceof Number steps
                            ? steps.intValue()
                            : 6;
                    double amount = request.amountUsd() != null ? request.amountUsd().doubleValue() : 0.0;
                    long latency = System.currentTimeMillis() - startTime;

                    return new AlertIngestResponse(
                            request.workflowId() != null ? request.workflowId() : String.valueOf(responseMap.getOrDefault("workflow_id", "gw-flow")),
                            status,
                            finalState,
                            totalSteps,
                            amount,
                            latency,
                            "CLOSED_HEALTHY"
                    );
                });

        if (circuitBreakerFactory != null) {
            ReactiveCircuitBreaker cb = circuitBreakerFactory.create("adkAgentService");
            return cb.run(call, ex -> fallbackInvestigation(request, startTime, ex));
        }

        return call.onErrorResume(ex -> fallbackInvestigation(request, startTime, ex));
    }

    public Mono<AlertIngestResponse> fallbackInvestigation(AlertIngestRequest request, long startTime, Throwable ex) {
        log.warn("Circuit Breaker Tripped! Routing to deterministic fallback heuristic. Cause: {}", ex.getMessage());

        boolean highRisk = request.amountUsd() != null && request.amountUsd().doubleValue() >= 500_000.0;
        String fallbackStatus = highRisk ? "FALLBACK_ESCALATED_TO_HUMAN" : "FALLBACK_TEMPORARY_HOLD";
        int state = highRisk ? 7 : 2;

        AlertIngestResponse fallback = new AlertIngestResponse(
                request.workflowId() != null ? request.workflowId() : "fallback-case",
                fallbackStatus,
                state,
                1,
                request.amountUsd() != null ? request.amountUsd().doubleValue() : 0.0,
                System.currentTimeMillis() - startTime,
                "OPEN_CIRCUIT_DEGRADED"
        );

        return Mono.just(fallback);
    }
}

