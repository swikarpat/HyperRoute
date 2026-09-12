package com.hyperroute.banking.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "payment_transactions", indexes = {
    @Index(name = "idx_payment_idempotency", columnList = "idempotency_key", unique = true)
})
public class PaymentTransaction {

    @Id
    @Column(name = "payment_id", length = 64, nullable = false)
    private String id;

    @Column(name = "idempotency_key", length = 128, unique = true, nullable = false)
    private String idempotencyKey;

    @Column(name = "source_account_id", length = 64, nullable = false)
    private String sourceAccountId;

    @Column(name = "destination_account_id", length = 64, nullable = false)
    private String destinationAccountId;

    @Column(name = "amount", precision = 19, scale = 2, nullable = false)
    private BigDecimal amount;

    @Column(name = "currency", length = 3, nullable = false)
    private String currency;

    @Enumerated(EnumType.STRING)
    @Column(name = "state", length = 32, nullable = false)
    private PaymentState state;

    @Column(name = "narrative", length = 512)
    private String narrative;

    @Column(name = "compliance_action", length = 64)
    private String complianceAction;

    @Column(name = "compliance_reason", length = 512)
    private String complianceReason;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    public PaymentTransaction() {}

    public PaymentTransaction(String id, String idempotencyKey, String sourceAccountId, String destinationAccountId,
                              BigDecimal amount, String currency, PaymentState state, String narrative) {
        this.id = id;
        this.idempotencyKey = idempotencyKey;
        this.sourceAccountId = sourceAccountId;
        this.destinationAccountId = destinationAccountId;
        this.amount = amount;
        this.currency = currency;
        this.state = state;
        this.narrative = narrative;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    public String getId() { return id; }
    public String getIdempotencyKey() { return idempotencyKey; }
    public String getSourceAccountId() { return sourceAccountId; }
    public String getDestinationAccountId() { return destinationAccountId; }
    public BigDecimal getAmount() { return amount; }
    public String getCurrency() { return currency; }
    public PaymentState getState() { return state; }
    public void setState(PaymentState state) { 
        this.state = state; 
        this.updatedAt = Instant.now();
    }
    public String getNarrative() { return narrative; }
    public String getComplianceAction() { return complianceAction; }
    public void setComplianceAction(String complianceAction) { this.complianceAction = complianceAction; }
    public String getComplianceReason() { return complianceReason; }
    public void setComplianceReason(String complianceReason) { this.complianceReason = complianceReason; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
