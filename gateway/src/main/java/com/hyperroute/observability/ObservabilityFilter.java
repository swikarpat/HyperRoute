package com.hyperroute.observability;

import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.cloud.gateway.support.ServerWebExchangeUtils;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Component
public class ObservabilityFilter implements WebFilter, Ordered {
    private static final Logger log = LoggerFactory.getLogger(ObservabilityFilter.class);
    private final ObservabilityMetrics metrics;
    private final Tracer tracer;

    public ObservabilityFilter(ObservabilityMetrics metrics, Tracer tracer) {
        this.metrics = metrics;
        this.tracer = tracer;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        long started = System.nanoTime();
        String clientId = exchange.getRequest().getHeaders().getFirst("X-API-Key");
        clientId = clientId == null || clientId.isBlank() ? "anonymous" : clientId;
        String route = exchange.getAttributeOrDefault(ServerWebExchangeUtils.GATEWAY_ROUTE_ATTR, "unmatched");
        String finalClientId = clientId;
        return chain.filter(exchange).doFinally(signal -> {
            String status = String.valueOf(exchange.getResponse().getStatusCode() == null
                ? 200 : exchange.getResponse().getStatusCode().value());
            String routeTier = route.contains("payments") ? "premium" : "standard";
            try (MDC.MDCCloseable ignoredClient = MDC.putCloseable("client_id", finalClientId);
                 MDC.MDCCloseable ignoredRoute = MDC.putCloseable("route_id", route)) {
                String traceparent = exchange.getRequest().getHeaders().getFirst("traceparent");
                if (traceparent != null && traceparent.length() >= 55) {
                    MDC.put("trace_id", traceparent.substring(3, 35));
                }
                if (tracer.currentSpan() != null) {
                    if (MDC.get("trace_id") == null) {
                        MDC.put("trace_id", tracer.currentSpan().context().traceId());
                    }
                    MDC.put("span_id", tracer.currentSpan().context().spanId());
                }
                metrics.ingressTimer(route, status, exchange.getRequest().getMethod().name())
                    .record(System.nanoTime() - started, java.util.concurrent.TimeUnit.NANOSECONDS);
                log.info("HTTP_REQUEST_COMPLETED status_code={} route_id={}", status, route);
                if (HttpStatus.TOO_MANY_REQUESTS.value() == Integer.parseInt(status)) {
                    metrics.recordRateLimitDrop(finalClientId, routeTier);
                    log.warn("RATE_LIMIT_EXCEEDED");
                }
            }
        });
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }
}