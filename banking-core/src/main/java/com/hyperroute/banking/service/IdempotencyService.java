package com.hyperroute.banking.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Distributed Idempotency Service using Redis with in-memory fallback.
 * Prevents double-charge and replay attacks on financial rails.
 */
@Service
public class IdempotencyService {

    private static final Logger log = LoggerFactory.getLogger(IdempotencyService.class);
    private static final Duration DEFAULT_TTL = Duration.ofSeconds(120);

    private final StringRedisTemplate redisTemplate;
    private final ConcurrentHashMap<String, String> localFallbackCache = new ConcurrentHashMap<>();

    public IdempotencyService(@Autowired(required = false) StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * Atomically acquires an idempotency lock for the given key.
     * @return true if lock acquired (new request), false if duplicate.
     */
    public boolean acquireLock(String idempotencyKey) {
        String key = "idempotency:" + idempotencyKey;
        try {
            if (redisTemplate != null) {
                Boolean success = redisTemplate.opsForValue().setIfAbsent(key, "IN_PROGRESS", DEFAULT_TTL);
                return Boolean.TRUE.equals(success);
            }
        } catch (Exception ex) {
            log.warn("[Idempotency] Redis unreachable, falling back to local memory cache: {}", ex.getMessage());
        }
        return localFallbackCache.putIfAbsent(key, "IN_PROGRESS") == null;
    }

    /**
     * Records the completed transaction result for future idempotent queries.
     */
    public void recordResult(String idempotencyKey, String resultJson) {
        String key = "idempotency:" + idempotencyKey;
        try {
            if (redisTemplate != null) {
                redisTemplate.opsForValue().set(key, resultJson, DEFAULT_TTL);
                return;
            }
        } catch (Exception ex) {
            log.warn("[Idempotency] Redis set failed: {}", ex.getMessage());
        }
        localFallbackCache.put(key, resultJson);
    }

    /**
     * Retrieves previous cached result if request was already processed.
     */
    public String getExistingResult(String idempotencyKey) {
        String key = "idempotency:" + idempotencyKey;
        try {
            if (redisTemplate != null) {
                return redisTemplate.opsForValue().get(key);
            }
        } catch (Exception ex) {
            // fallback
        }
        return localFallbackCache.get(key);
    }
}
