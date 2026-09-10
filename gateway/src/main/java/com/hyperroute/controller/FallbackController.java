package com.hyperroute.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Map;

@RestController
@RequestMapping("/fallback")
public class FallbackController {
    private static final Logger log = LoggerFactory.getLogger(FallbackController.class);

    @GetMapping("/payments")
    public Mono<ResponseEntity<Map<String, Object>>> paymentsFallback() {
        log.warn("BACKEND_FALLBACK_INVOCATION backend_service=payments");
        return Mono.just(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(
            Map.of(
                "error", "CIRCUIT_BREAKER_ACTIVE",
                "message", "Downstream payment provider failed. Graceful fallback engaged.",
                "status", 503,
                "timestamp", Instant.now().toString()
            )
        ));
    }
}
