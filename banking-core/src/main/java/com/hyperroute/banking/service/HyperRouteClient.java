package com.hyperroute.banking.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.Map;

/**
 * Synchronous REST Client for HyperRoute Gateway (:8080).
 * Dispatches pre-settlement compliance screening requests with strict timeout SLAs.
 */
@Component
public class HyperRouteClient {

    private static final Logger log = LoggerFactory.getLogger(HyperRouteClient.class);

    private final RestClient restClient;

    public record ComplianceDecision(
        String status,
        String circuitBreakerStatus,
        Integer gatewayLatencyMs,
        Integer finalFsmState,
        String reason
    ) {}

    public HyperRouteClient(@Value("${hyperroute.gateway.url:http://127.0.0.1:8080}") String gatewayUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) Duration.ofMillis(500).toMillis());
        factory.setReadTimeout((int) Duration.ofMillis(3000).toMillis());

        this.restClient = RestClient.builder()
            .baseUrl(gatewayUrl)
            .requestFactory(factory)
            .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .defaultHeader("X-API-Key", "hyperroute-core-banking-key")
            .build();
    }

    public ComplianceDecision screenTransfer(String accountId, double amountUsd, String senderCountry,
                                            String receiverCountry, String narrative) {
        Map<String, Object> payload = Map.of(
            "account_id", accountId,
            "amount_usd", amountUsd,
            "sender_country", senderCountry != null ? senderCountry : "US",
            "receiver_country", receiverCountry != null ? receiverCountry : "US",
            "narrative", narrative != null ? narrative : "Wire transfer"
        );

        try {
            log.info("[HyperRoute Client] Dispatching screening alert for account {} amount ${}", accountId, amountUsd);
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restClient.post()
                .uri("/api/v1/gateway/alerts")
                .body(payload)
                .retrieve()
                .body(Map.class);

            if (response != null) {
                String status = String.valueOf(response.getOrDefault("status", "UNKNOWN"));
                String cbStatus = String.valueOf(response.getOrDefault("circuit_breaker_status", "UNKNOWN"));
                Integer latency = response.get("gateway_latency_ms") instanceof Number n ? n.intValue() : 0;
                Integer fsmState = response.get("final_fsm_state") instanceof Number n ? n.intValue() : 0;
                String reason = String.valueOf(response.getOrDefault("reason", "Screened by HyperRoute"));

                log.info("[HyperRoute Client] Decision received: status={} fsmState={} in {}ms", status, fsmState, latency);
                return new ComplianceDecision(status, cbStatus, latency, fsmState, reason);
            }
        } catch (Exception ex) {
            log.warn("[HyperRoute Client] Failed to contact gateway: {}. Engaging fail-safe hold.", ex.getMessage());
        }

        // Deterministic FinTech fail-safe hold
        return new ComplianceDecision(
            "FALLBACK_TEMPORARY_HOLD",
            "CIRCUIT_BREAKER_ACTIVE",
            0,
            7, // State 7: AWAITING_HUMAN_APPROVAL
            "HyperRoute Gateway offline or timed out; held safely for human review"
        );
    }
}
