package com.hyperroute;

import com.hyperroute.model.AlertIngestRequest;
import com.hyperroute.model.AlertIngestResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
    properties = {
        "spring.data.redis.host=127.0.0.1",
        "spring.cloud.gateway.discovery.locator.enabled=false",
        "hyperroute.agent-runtime-url=http://localhost:59999" // intentionally offline port to verify circuit breaker
    })
class GatewayIngressControllerTest {

    @LocalServerPort
    int port;

    @Autowired
    WebClient.Builder webClientBuilder;

    @Test
    void testIngestAlertFallbackWhenDownstreamOffline() {
        AlertIngestRequest request = new AlertIngestRequest(
            "ACC-CORP-9981",
            BigDecimal.valueOf(1_500_000.00),
            "SG",
            "US",
            "High value corporate cross-border wire transfer.",
            "test-wf-001"
        );

        AlertIngestResponse response = client().post()
            .uri("/api/v1/gateway/alerts")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .bodyToMono(AlertIngestResponse.class)
            .block();

        assertThat(response).isNotNull();
        assertThat(response.workflowId()).isEqualTo("test-wf-001");
        // For amount >= $500k, fallback state is 7 (Awaiting human approval)
        assertThat(response.finalFsmState()).isEqualTo(7);
        assertThat(response.status()).isEqualTo("FALLBACK_ESCALATED_TO_HUMAN");
        assertThat(response.circuitBreakerStatus()).isEqualTo("OPEN_CIRCUIT_DEGRADED");
    }

    @Test
    void testIngestAlertLowValueFallback() {
        AlertIngestRequest request = new AlertIngestRequest(
            "ACC-RETAIL-1122",
            BigDecimal.valueOf(25_000.00),
            "US",
            "US",
            "Routine payroll transfer.",
            "test-wf-002"
        );

        AlertIngestResponse response = client().post()
            .uri("/api/v1/gateway/alerts")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .bodyToMono(AlertIngestResponse.class)
            .block();

        assertThat(response).isNotNull();
        assertThat(response.workflowId()).isEqualTo("test-wf-002");
        assertThat(response.finalFsmState()).isEqualTo(2);
        assertThat(response.status()).isEqualTo("FALLBACK_TEMPORARY_HOLD");
        assertThat(response.circuitBreakerStatus()).isEqualTo("OPEN_CIRCUIT_DEGRADED");
    }

    private WebClient client() {
        return webClientBuilder.baseUrl("http://localhost:" + port).build();
    }
}

