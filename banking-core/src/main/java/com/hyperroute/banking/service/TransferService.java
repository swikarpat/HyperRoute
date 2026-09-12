package com.hyperroute.banking.service;

import com.hyperroute.banking.domain.*;
import com.hyperroute.banking.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * Enterprise Transfer Service orchestrating:
 * 1. Redis Distributed Idempotency Lock
 * 2. NoSQL ISO 20022 Polymorphic Document Storage
 * 3. Relational PostgreSQL/H2 ACID Double-Entry Bookkeeping
 * 4. HyperRoute Synchronous Compliance Gate Screening
 * 5. Transactional Outbox Kafka Event Emission
 */
@Service
public class TransferService {

    private static final Logger log = LoggerFactory.getLogger(TransferService.class);
    public static final String ESCROW_ACCOUNT_ID = "ACC-ESCROW-HOLD";

    private final AccountRepository accountRepo;
    private final LedgerEntryRepository ledgerRepo;
    private final PaymentTransactionRepository paymentRepo;
    private final OutboxEventRepository outboxRepo;
    private final NoSqlDocumentRepository documentRepo;
    private final IdempotencyService idempotencyService;
    private final HyperRouteClient hyperRouteClient;

    public record TransferRequest(
        String sourceAccountId,
        String destinationAccountId,
        BigDecimal amount,
        String currency,
        String narrative,
        String senderCountry,
        String receiverCountry,
        String clientIp,
        String deviceFingerprint,
        String rawIso20022Payload
    ) {}

    public record TransferResponse(
        String paymentId,
        String idempotencyKey,
        PaymentState state,
        String complianceStatus,
        Integer finalFsmState,
        Integer latencyMs,
        String message
    ) {}

    public TransferService(
        AccountRepository accountRepo,
        LedgerEntryRepository ledgerRepo,
        PaymentTransactionRepository paymentRepo,
        OutboxEventRepository outboxRepo,
        NoSqlDocumentRepository documentRepo,
        IdempotencyService idempotencyService,
        HyperRouteClient hyperRouteClient
    ) {
        this.accountRepo = accountRepo;
        this.ledgerRepo = ledgerRepo;
        this.paymentRepo = paymentRepo;
        this.outboxRepo = outboxRepo;
        this.documentRepo = documentRepo;
        this.idempotencyService = idempotencyService;
        this.hyperRouteClient = hyperRouteClient;
    }

    @Transactional(isolation = Isolation.READ_COMMITTED)
    public TransferResponse executeTransfer(String idempotencyKey, TransferRequest request) {
        // 1. Distributed Idempotency Check
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            idempotencyKey = UUID.randomUUID().toString();
        }

        boolean lockAcquired = idempotencyService.acquireLock(idempotencyKey);
        if (!lockAcquired) {
            log.warn("[Idempotency Intercept] Duplicate transfer attempt with key: {}", idempotencyKey);
            return paymentRepo.findByIdempotencyKey(idempotencyKey)
                .map(tx -> new TransferResponse(
                    tx.getId(),
                    tx.getIdempotencyKey(),
                    tx.getState(),
                    tx.getComplianceAction(),
                    9,
                    0,
                    "IDEMPOTENT_DUPLICATE: Previously processed as " + tx.getState()
                ))
                .orElse(new TransferResponse(
                    "IN_PROGRESS",
                    idempotencyKey,
                    PaymentState.INITIATED,
                    "IN_PROGRESS",
                    0,
                    0,
                    "Request currently processing concurrently"
                ));
        }

        String paymentId = "PAY-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        Money transferMoney = new Money(request.amount(), request.currency() != null ? request.currency() : "USD");

        // 2. Store Polymorphic Raw ISO 20022 Payload in NoSQL Document Store
        NoSqlPaymentDocument doc = new NoSqlPaymentDocument(
            paymentId,
            "pacs.008.001.10",
            request.rawIso20022Payload() != null ? request.rawIso20022Payload() : "{\"GrpHdr\":{\"MsgId\":\"" + paymentId + "\"}}",
            request.deviceFingerprint() != null ? request.deviceFingerprint() : "fp-browser-sec-99",
            request.clientIp() != null ? request.clientIp() : "127.0.0.1",
            Map.of("narrative", request.narrative() != null ? request.narrative() : "Standard Transfer"),
            Instant.now()
        );
        documentRepo.save(doc);

        // 3. Relational Pessimistic Lock on Debtor Account
        Account sourceAccount = accountRepo.findByIdWithLock(request.sourceAccountId())
            .orElseThrow(() -> new IllegalArgumentException("Source account not found: " + request.sourceAccountId()));

        Account destAccount = accountRepo.findByIdWithLock(request.destinationAccountId())
            .orElseThrow(() -> new IllegalArgumentException("Destination account not found: " + request.destinationAccountId()));

        // Validate Sufficient Balance
        if (!sourceAccount.toMoney().isGreaterThanOrEqual(transferMoney)) {
            PaymentTransaction failedTx = new PaymentTransaction(
                paymentId, idempotencyKey, sourceAccount.getId(), destAccount.getId(),
                transferMoney.amount(), transferMoney.currency(), PaymentState.REJECTED,
                "INSUFFICIENT_FUNDS"
            );
            paymentRepo.save(failedTx);
            return new TransferResponse(
                paymentId, idempotencyKey, PaymentState.REJECTED, "REJECTED_BALANCE", 0, 0,
                "Insufficient funds: available $" + sourceAccount.getBalance() + ", requested $" + transferMoney.amount()
            );
        }

        // 4. Stage Transfer & Write Transactional Outbox Event (PAYMENT_INITIATED)
        PaymentTransaction payment = new PaymentTransaction(
            paymentId, idempotencyKey, sourceAccount.getId(), destAccount.getId(),
            transferMoney.amount(), transferMoney.currency(), PaymentState.PENDING_COMPLIANCE,
            request.narrative()
        );
        paymentRepo.save(payment);

        OutboxEvent initiatedEvent = new OutboxEvent(
            "PaymentTransaction", paymentId, "PAYMENT_INITIATED",
            String.format("{\"paymentId\":\"%s\",\"amount\":%s,\"currency\":\"%s\"}",
                paymentId, transferMoney.amount(), transferMoney.currency())
        );
        outboxRepo.save(initiatedEvent);

        // 5. Synchronous Pre-Settlement Screening through HyperRoute Gateway (:8080)
        HyperRouteClient.ComplianceDecision decision = hyperRouteClient.screenTransfer(
            sourceAccount.getId(),
            transferMoney.amount().doubleValue(),
            request.senderCountry(),
            request.receiverCountry(),
            request.narrative()
        );

        payment.setComplianceAction(decision.status());
        payment.setComplianceReason(decision.reason());

        TransferResponse response;

        // 6. Act on Deterministic Compliance Decision
        if ("CLEAR_TRANSACTION".equalsIgnoreCase(decision.status())) {
            // Strict Double-Entry Ledger Bookkeeping Invariant: Sum(Debits) == Sum(Credits)
            sourceAccount.setBalance(sourceAccount.toMoney().subtract(transferMoney).amount());
            destAccount.setBalance(destAccount.toMoney().add(transferMoney).amount());
            accountRepo.save(sourceAccount);
            accountRepo.save(destAccount);

            LedgerEntry debitEntry = new LedgerEntry(
                paymentId, sourceAccount.getId(), LedgerEntry.EntryType.DEBIT,
                transferMoney.amount(), transferMoney.currency(),
                "Transfer to " + destAccount.getAccountNumber() + ": " + request.narrative()
            );
            LedgerEntry creditEntry = new LedgerEntry(
                paymentId, destAccount.getId(), LedgerEntry.EntryType.CREDIT,
                transferMoney.amount(), transferMoney.currency(),
                "Transfer from " + sourceAccount.getAccountNumber() + ": " + request.narrative()
            );
            ledgerRepo.save(debitEntry);
            ledgerRepo.save(creditEntry);

            payment.setState(PaymentState.SETTLED);
            paymentRepo.save(payment);

            OutboxEvent settledEvent = new OutboxEvent(
                "PaymentTransaction", paymentId, "PAYMENT_SETTLED",
                String.format("{\"paymentId\":\"%s\",\"fsmState\":%d,\"status\":\"SETTLED\"}",
                    paymentId, decision.finalFsmState())
            );
            outboxRepo.save(settledEvent);

            response = new TransferResponse(
                paymentId, idempotencyKey, PaymentState.SETTLED, decision.status(),
                decision.finalFsmState(), decision.gatewayLatencyMs(), "Payment settled successfully"
            );
        } else {
            // Suspicious / Structuring / High-Value Wire: Hold Funds in Escrow Suspense
            sourceAccount.setBalance(sourceAccount.toMoney().subtract(transferMoney).amount());
            accountRepo.save(sourceAccount);

            Account escrowAccount = accountRepo.findById(ESCROW_ACCOUNT_ID)
                .orElseGet(() -> accountRepo.save(new Account(
                    ESCROW_ACCOUNT_ID, "9999-ESCROW-01", "Compliance Escrow Reserve",
                    BigDecimal.ZERO, "USD", "ESCROW_SYSTEM"
                )));
            escrowAccount.setBalance(escrowAccount.toMoney().add(transferMoney).amount());
            accountRepo.save(escrowAccount);

            LedgerEntry holdDebit = new LedgerEntry(
                paymentId, sourceAccount.getId(), LedgerEntry.EntryType.DEBIT,
                transferMoney.amount(), transferMoney.currency(),
                "Compliance Hold to Escrow: " + decision.reason()
            );
            LedgerEntry holdCredit = new LedgerEntry(
                paymentId, escrowAccount.getId(), LedgerEntry.EntryType.CREDIT,
                transferMoney.amount(), transferMoney.currency(),
                "Escrow Hold Credit for Payment " + paymentId
            );
            ledgerRepo.save(holdDebit);
            ledgerRepo.save(holdCredit);

            payment.setState(PaymentState.FROZEN);
            paymentRepo.save(payment);

            OutboxEvent holdEvent = new OutboxEvent(
                "PaymentTransaction", paymentId, "PAYMENT_HELD",
                String.format("{\"paymentId\":\"%s\",\"fsmState\":%d,\"action\":\"%s\",\"reason\":\"%s\"}",
                    paymentId, decision.finalFsmState(), decision.status(), decision.reason())
            );
            outboxRepo.save(holdEvent);

            response = new TransferResponse(
                paymentId, idempotencyKey, PaymentState.FROZEN, decision.status(),
                decision.finalFsmState(), decision.gatewayLatencyMs(),
                "Transfer placed on regulatory compliance hold: " + decision.reason()
            );
        }

        // Record in cache for idempotency replays
        idempotencyService.recordResult(idempotencyKey, response.toString());
        return response;
    }
}
