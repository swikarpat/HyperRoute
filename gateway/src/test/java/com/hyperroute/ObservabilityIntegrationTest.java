package com.hyperroute;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.web.reactive.function.client.WebClient;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
    properties = {
        "spring.data.redis.host=127.0.0.1",
        "spring.cloud.gateway.discovery.locator.enabled=false"
    })
@ExtendWith(OutputCaptureExtension.class)
class ObservabilityIntegrationTest {
    @LocalServerPort
    int port;

    @Autowired
    WebClient.Builder webClientBuilder;

    @Test
    void prometheusExposesHyperRouteMetrics() {
        String body = client().get()
            .uri("/actuator/prometheus")
            .retrieve()
            .bodyToMono(String.class)
            .block();

        assertThat(body).as("ingress timer").contains("hyperroute_ingress_duration_seconds");
        assertThat(body).as("rate-limit counter").contains("hyperroute_ratelimit_drops_total");
        assertThat(body).as("circuit-breaker gauge").contains("hyperroute_circuit_breaker_state");
        assertThat(body).as("cache hit counter").contains("hyperroute_redis_cache_hits_total");
        assertThat(body).as("cache miss counter").contains("hyperroute_redis_cache_misses_total");
    }

    @Test
    void traceparentIsCopiedToLoggingMdc(CapturedOutput output) {
        String traceId = "0123456789abcdef0123456789abcdef";
        client().get()
            .uri("/actuator/health")
            .header("traceparent", "00-" + traceId + "-0123456789abcdef-01")
            .retrieve()
            .toBodilessEntity()
            .block();

        assertThat(output).contains(traceId);
    }

    private WebClient client() {
        return webClientBuilder.baseUrl("http://localhost:" + port).build();
    }
}