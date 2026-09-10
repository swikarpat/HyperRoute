package com.hyperroute.observability;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class ObservabilityMetrics {
    private static final Logger log = LoggerFactory.getLogger(ObservabilityMetrics.class);
    private final MeterRegistry registry;
    private final CircuitBreakerRegistry circuitBreakerRegistry;
    private final ConcurrentHashMap<String, AtomicInteger> circuitStates = new ConcurrentHashMap<>();

    public ObservabilityMetrics(MeterRegistry registry, CircuitBreakerRegistry circuitBreakerRegistry) {
        this.registry = registry;
        this.circuitBreakerRegistry = circuitBreakerRegistry;
        ingressTimer("unmatched", "200", "UNKNOWN");
        Counter.builder("hyperroute_ratelimit_drops_total")
            .description("Requests rejected by the distributed rate limiter")
            .tags("client_id", "unmatched", "route_tier", "unknown")
            .register(registry);
        registry.counter("hyperroute_redis_cache_hits_total");
        registry.counter("hyperroute_redis_cache_misses_total");
    }

    @PostConstruct
    void observeCircuitBreakers() {
        circuitBreakerRegistry.getAllCircuitBreakers().forEach(this::observeCircuitBreaker);
    }

    private void observeCircuitBreaker(CircuitBreaker circuitBreaker) {
        setCircuitState(circuitBreaker.getName(), stateValue(circuitBreaker.getState()));
        circuitBreaker.getEventPublisher().onStateTransition(event -> {
            setCircuitState(event.getCircuitBreakerName(), stateValue(event.getStateTransition().getToState()));
            log.warn("CIRCUIT_BREAKER_TRIPPED backend_service={} state={}",
                event.getCircuitBreakerName(), event.getStateTransition().getToState());
        });
    }

    private int stateValue(CircuitBreaker.State state) {
        return switch (state) {
            case CLOSED -> 0;
            case HALF_OPEN -> 1;
            case OPEN -> 2;
            default -> 0;
        };
    }

    public Timer ingressTimer(String route, String statusCode, String method) {
        return Timer.builder("hyperroute_ingress_duration_seconds")
            .description("HyperRoute ingress request latency")
            .tags("route", route, "status_code", statusCode, "http_method", method)
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);
    }

    public void recordRateLimitDrop(String clientId, String routeTier) {
        Counter.builder("hyperroute_ratelimit_drops_total")
            .description("Requests rejected by the distributed rate limiter")
            .tags("client_id", clientId, "route_tier", routeTier)
            .register(registry)
            .increment();
    }

    public void recordCacheHit() {
        registry.counter("hyperroute_redis_cache_hits_total").increment();
    }

    public void recordCacheMiss() {
        registry.counter("hyperroute_redis_cache_misses_total").increment();
        log.warn("CACHE_MISS backend=redis");
    }

    public void setCircuitState(String backendService, int state) {
        AtomicInteger value = circuitStates.computeIfAbsent(backendService, service -> {
            AtomicInteger stateValue = new AtomicInteger();
            registry.gauge("hyperroute_circuit_breaker_state",
                java.util.List.of(io.micrometer.core.instrument.Tag.of("backend_service", service)), stateValue);
            return stateValue;
        });
        value.set(state);
    }
}