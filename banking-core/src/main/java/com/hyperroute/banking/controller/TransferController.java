package com.hyperroute.banking.controller;

import com.hyperroute.banking.domain.*;
import com.hyperroute.banking.repository.*;
import com.hyperroute.banking.service.TransferService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/core")
public class TransferController {

    private final TransferService transferService;
    private final AccountRepository accountRepo;
    private final LedgerEntryRepository ledgerRepo;
    private final PaymentTransactionRepository paymentRepo;
    private final OutboxEventRepository outboxRepo;
    private final NoSqlDocumentRepository documentRepo;

    public TransferController(
        TransferService transferService,
        AccountRepository accountRepo,
        LedgerEntryRepository ledgerRepo,
        PaymentTransactionRepository paymentRepo,
        OutboxEventRepository outboxRepo,
        NoSqlDocumentRepository documentRepo
    ) {
        this.transferService = transferService;
        this.accountRepo = accountRepo;
        this.ledgerRepo = ledgerRepo;
        this.paymentRepo = paymentRepo;
        this.outboxRepo = outboxRepo;
        this.documentRepo = documentRepo;
    }

    /**
     * Executes a new financial transfer under strict double-entry and compliance gates.
     */
    @PostMapping("/transfers")
    public ResponseEntity<TransferService.TransferResponse> initiateTransfer(
        @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey,
        @RequestBody TransferService.TransferRequest request
    ) {
        TransferService.TransferResponse response = transferService.executeTransfer(idempotencyKey, request);
        return ResponseEntity.ok(response);
    }

    /**
     * Query status of an existing payment transaction.
     */
    @GetMapping("/transfers/{id}")
    public ResponseEntity<PaymentTransaction> getTransfer(@PathVariable String id) {
        return paymentRepo.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * List all accounts and current ledger balances.
     */
    @GetMapping("/accounts")
    public ResponseEntity<List<Account>> listAccounts() {
        return ResponseEntity.ok(accountRepo.findAll());
    }

    /**
     * Query double-entry ledger journal for a specific account.
     */
    @GetMapping("/accounts/{id}/statement")
    public ResponseEntity<Map<String, Object>> getAccountStatement(@PathVariable String id) {
        Account account = accountRepo.findById(id).orElse(null);
        if (account == null) {
            return ResponseEntity.notFound().build();
        }
        List<LedgerEntry> entries = ledgerRepo.findByAccountIdOrderByCreatedAtDesc(id);
        return ResponseEntity.ok(Map.of(
            "account", account,
            "totalEntries", entries.size(),
            "ledgerEntries", entries
        ));
    }

    /**
     * Query the NoSQL polymorphic document for a payment (ISO 20022 raw payload & forensics).
     */
    @GetMapping("/documents/{paymentId}")
    public ResponseEntity<NoSqlPaymentDocument> getPaymentDocument(@PathVariable String paymentId) {
        return documentRepo.findById(paymentId)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Query the Transactional Outbox table (System of Record -> Kafka event log).
     */
    @GetMapping("/outbox")
    public ResponseEntity<List<OutboxEvent>> getOutboxEvents() {
        return ResponseEntity.ok(outboxRepo.findAll());
    }
}

