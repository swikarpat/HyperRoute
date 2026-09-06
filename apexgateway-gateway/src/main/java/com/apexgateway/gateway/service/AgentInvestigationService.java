package com.apexgateway.gateway.service;

import com.apexgateway.gateway.model.AlertIngestRequest;
import com.apexgateway.gateway.model.AlertIngestResponse;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Service
public class AgentInvestigationService {

    private static final Logger log = LoggerFactory.getLogger(AgentInvestigationService.class);
    private final WebClient webClient;

    public AgentInvestigationService(
            WebClient.Builder webClientBuilder,
            @Value("${apexgateway.agent-runtime-url}") String agentRuntimeUrl) {
        this.webClient = webClientBuilder
                .baseUrl(agentRuntimeUrl)
                .build();
    }

    @CircuitBreaker(name = "adkAgentService", fallbackMethod = "fallbackInvestigation")
    public Mono<AlertIngestResponse> dispatchInvestigation(AlertIngestRequest request, long startTime) {
        return webClient.post()
                .uri("/api/v1/investigate")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AlertIngestResponse.class)
                .timeout(Duration.ofSeconds(5))
                .map(response -> new AlertIngestResponse(
                        response.workflowId(),
                        response.status(),
                        response.finalFsmState(),
                        response.totalStepsExecuted(),
                        response.transactionAmount(),
                        System.currentTimeMillis() - startTime,
                        "CLOSED_HEALTHY"));
    }

    public Mono<AlertIngestResponse> fallbackInvestigation(AlertIngestRequest request, long startTime, Throwable ex) {
        log.warn("Circuit Breaker Tripped! Routing to deterministic fallback heuristic. Cause: {}", ex.getMessage());

        boolean highRisk = request.amountUsd().doubleValue() >= 500_000.0;
        String fallbackStatus = highRisk ? "FALLBACK_ESCALATED_TO_HUMAN" : "FALLBACK_TEMPORARY_HOLD";
        int state = highRisk ? 7 : 2;

        AlertIngestResponse fallback = new AlertIngestResponse(
                request.workflowId() != null ? request.workflowId() : "fallback-case",
                fallbackStatus,
                state,
                1,
                request.amountUsd().doubleValue(),
                System.currentTimeMillis() - startTime,
                "OPEN_CIRCUIT_DEGRADED");

        return Mono.just(fallback);
    }
}