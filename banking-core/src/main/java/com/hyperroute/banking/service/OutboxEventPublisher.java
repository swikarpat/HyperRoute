package com.hyperroute.banking.service;

import com.hyperroute.banking.domain.OutboxEvent;
import com.hyperroute.banking.repository.OutboxEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

/**
 * Transactional Outbox Worker: Streams pending database events to Apache Kafka.
 * Guarantees at-least-once delivery between PostgreSQL/H2 System of Record and Kafka.
 */
@Component
public class OutboxEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(OutboxEventPublisher.class);
    private static final String DEFAULT_TOPIC = "core.payments.events";

    private final OutboxEventRepository outboxRepo;
    private final KafkaTemplate<String, String> kafkaTemplate;

    public OutboxEventPublisher(
        OutboxEventRepository outboxRepo,
        @Autowired(required = false) KafkaTemplate<String, String> kafkaTemplate
    ) {
        this.outboxRepo = outboxRepo;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelayString = "${banking.outbox.poll-interval-ms:3000}")
    @Transactional
    public void publishPendingEvents() {
        List<OutboxEvent> pending = outboxRepo.findTop50ByStatusOrderByCreatedAtAsc(OutboxEvent.EventStatus.PENDING);
        if (pending.isEmpty()) {
            return;
        }

        for (OutboxEvent event : pending) {
            try {
                if (kafkaTemplate != null) {
                    kafkaTemplate.send(DEFAULT_TOPIC, event.getAggregateId(), event.getPayloadJson())
                        .whenComplete((result, ex) -> {
                            if (ex == null) {
                                event.setStatus(OutboxEvent.EventStatus.PUBLISHED);
                                event.setPublishedAt(Instant.now());
                                outboxRepo.save(event);
                                log.info("[Outbox -> Kafka] Event published: ID={} Type={}", event.getId(), event.getEventType());
                            } else {
                                log.warn("[Outbox -> Kafka] Kafka publish error for {}: {}", event.getId(), ex.getMessage());
                            }
                        });
                } else {
                    // Local / Test simulation mode: mark published
                    event.setStatus(OutboxEvent.EventStatus.PUBLISHED);
                    event.setPublishedAt(Instant.now());
                    outboxRepo.save(event);
                    log.debug("[Outbox Sim] Marked event {} published in local standalone mode", event.getId());
                }
            } catch (Exception ex) {
                log.warn("[Outbox -> Kafka] Failed to dispatch event {}: {}", event.getId(), ex.getMessage());
            }
        }
    }
}
