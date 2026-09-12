package com.hyperroute.banking.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "ledger_entries", indexes = {
    @Index(name = "idx_ledger_account", columnList = "account_id"),
    @Index(name = "idx_ledger_tx", columnList = "transaction_id")
})
public class LedgerEntry {

    public enum EntryType { DEBIT, CREDIT }

    @Id
    @Column(name = "entry_id", length = 64, nullable = false)
    private String id;

    @Column(name = "transaction_id", length = 64, nullable = false)
    private String transactionId;

    @Column(name = "account_id", length = 64, nullable = false)
    private String accountId;

    @Enumerated(EnumType.STRING)
    @Column(name = "entry_type", length = 16, nullable = false)
    private EntryType type;

    @Column(name = "amount", precision = 19, scale = 2, nullable = false)
    private BigDecimal amount;

    @Column(name = "currency", length = 3, nullable = false)
    private String currency;

    @Column(name = "description", length = 255)
    private String description;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public LedgerEntry() {}

    public LedgerEntry(String transactionId, String accountId, EntryType type, BigDecimal amount, String currency, String description) {
        this.id = UUID.randomUUID().toString();
        this.transactionId = transactionId;
        this.accountId = accountId;
        this.type = type;
        this.amount = amount;
        this.currency = currency;
        this.description = description;
        this.createdAt = Instant.now();
    }

    public String getId() { return id; }
    public String getTransactionId() { return transactionId; }
    public String getAccountId() { return accountId; }
    public EntryType getType() { return type; }
    public BigDecimal getAmount() { return amount; }
    public String getCurrency() { return currency; }
    public String getDescription() { return description; }
    public Instant getCreatedAt() { return createdAt; }
}
