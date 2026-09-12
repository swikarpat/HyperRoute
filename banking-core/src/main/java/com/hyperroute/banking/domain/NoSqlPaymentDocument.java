package com.hyperroute.banking.domain;

import java.time.Instant;
import java.util.Map;

/**
 * NoSQL polymorphic document representing raw ISO 20022 messages and forensics.
 * In production this maps to Amazon DynamoDB / MongoDB.
 */
public record NoSqlPaymentDocument(
    String paymentId,
    String messageType, // e.g. "pacs.008.001.10"
    String rawPayload,  // Full ISO 20022 JSON/XML
    String deviceFingerprint,
    String clientIp,
    Map<String, Object> complianceMetadata,
    Instant receivedAt
) {}
