package com.hyperroute.banking;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = {
    "spring.kafka.bootstrap-servers=localhost:9092",
    "spring.data.redis.host=localhost",
    "management.health.redis.enabled=false"
})
class BankingCoreApplicationTests {

    @Test
    void contextLoads() {
        // Verifies the entire Spring Boot context with Virtual Threads, JPA, Redis, and Outbox loads cleanly.
    }
}

