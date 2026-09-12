package com.hyperroute.banking.repository;

import com.hyperroute.banking.domain.NoSqlPaymentDocument;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * NoSQL Document repository simulating Amazon DynamoDB / MongoDB for raw polymorphic ISO 20022 payloads.
 */
@Repository
public class NoSqlDocumentRepository {

    private final ConcurrentHashMap<String, NoSqlPaymentDocument> store = new ConcurrentHashMap<>();

    public void save(NoSqlPaymentDocument document) {
        if (document != null && document.paymentId() != null) {
            store.put(document.paymentId(), document);
        }
    }

    public Optional<NoSqlPaymentDocument> findById(String paymentId) {
        return Optional.ofNullable(store.get(paymentId));
    }

    public Collection<NoSqlPaymentDocument> findAll() {
        return store.values();
    }

    public long count() {
        return store.size();
    }
}

