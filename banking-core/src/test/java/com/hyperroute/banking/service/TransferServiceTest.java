package com.hyperroute.banking.service;

import com.hyperroute.banking.domain.*;
import com.hyperroute.banking.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.TestPropertySource;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;

@SpringBootTest
@TestPropertySource(properties = {
    "spring.kafka.bootstrap-servers=localhost:9092",
    "spring.data.redis.host=localhost",
    "management.health.redis.enabled=false"
})
public class TransferServiceTest {

    @Autowired
    private TransferService transferService;

    @Autowired
    private AccountRepository accountRepo;

    @Autowired
    private LedgerEntryRepository ledgerRepo;

    @Autowired
    private PaymentTransactionRepository paymentRepo;

    @Autowired
    private OutboxEventRepository outboxRepo;

    @Autowired
    private NoSqlDocumentRepository documentRepo;

    @MockBean
    private HyperRouteClient hyperRouteClient;

    private static final String SENDER_ID = "ACC-TEST-SENDER";
    private static final String RECEIVER_ID = "ACC-TEST-RECEIVER";

    @BeforeEach
    void setUp() {
        ledgerRepo.deleteAll();
        paymentRepo.deleteAll();
        outboxRepo.deleteAll();
        accountRepo.deleteAll();

        accountRepo.save(new Account(
            SENDER_ID, "ACC-NUM-SENDER", "Alice Test",
            BigDecimal.valueOf(10000.00), "USD", "ACTIVE"
        ));
        accountRepo.save(new Account(
            RECEIVER_ID, "ACC-NUM-RECEIVER", "Bob Merchant",
            BigDecimal.valueOf(500.00), "USD", "ACTIVE"
        ));
    }

    @Test
    @DisplayName("Test 1: Successful transfer enforces Double-Entry Invariant and Outbox Event")
    void testSuccessfulTransferDoubleEntry() {
        // Mock HyperRoute approving transfer (State 9: ISSUING_CLEARANCE)
        Mockito.when(hyperRouteClient.screenTransfer(anyString(), anyDouble(), anyString(), anyString(), anyString()))
            .thenReturn(new HyperRouteClient.ComplianceDecision("CLEAR_TRANSACTION", "CLOSED_HEALTHY", 3, 9, "Cleared"));

        String idempotencyKey = "key-" + UUID.randomUUID();
        TransferService.TransferRequest req = new TransferService.TransferRequest(
            SENDER_ID, RECEIVER_ID, BigDecimal.valueOf(1500.00), "USD",
            "Monthly contract fee", "US", "US", "127.0.0.1", "fp-test-1",
            "{\"GrpHdr\":{\"MsgId\":\"TEST-001\"}}"
        );

        TransferService.TransferResponse resp = transferService.executeTransfer(idempotencyKey, req);

        assertNotNull(resp.paymentId());
        assertEquals(PaymentState.SETTLED, resp.state());
        assertEquals("CLEAR_TRANSACTION", resp.complianceStatus());

        // 1. Verify Balances updated correctly
        Account sender = accountRepo.findById(SENDER_ID).orElseThrow();
        Account receiver = accountRepo.findById(RECEIVER_ID).orElseThrow();
        assertEquals(new BigDecimal("8500.00"), sender.getBalance());
        assertEquals(new BigDecimal("2000.00"), receiver.getBalance());

        // 2. Verify Double-Entry Journal Invariant: Sum(Debits) == Sum(Credits)
        List<LedgerEntry> entries = ledgerRepo.findByTransactionId(resp.paymentId());
        assertEquals(2, entries.size());

        BigDecimal totalDebits = entries.stream()
            .filter(e -> e.getType() == LedgerEntry.EntryType.DEBIT)
            .map(LedgerEntry::getAmount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        BigDecimal totalCredits = entries.stream()
            .filter(e -> e.getType() == LedgerEntry.EntryType.CREDIT)
            .map(LedgerEntry::getAmount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        assertEquals(totalDebits, totalCredits, "Double-entry accounting invariant violated: debits must equal credits");
        assertEquals(new BigDecimal("1500.00"), totalDebits);

        // 3. Verify NoSQL Document stored
        assertTrue(documentRepo.findById(resp.paymentId()).isPresent());

        // 4. Verify Transactional Outbox Event produced
        List<OutboxEvent> outbox = outboxRepo.findAll().stream()
            .filter(e -> e.getAggregateId().equals(resp.paymentId()))
            .toList();
        assertFalse(outbox.isEmpty());
    }

    @Test
    @DisplayName("Test 2: Insufficient funds rejects transfer without ledger mutation")
    void testInsufficientFundsRejection() {
        String idempotencyKey = "key-insufficient-" + UUID.randomUUID();
        TransferService.TransferRequest req = new TransferService.TransferRequest(
            SENDER_ID, RECEIVER_ID, BigDecimal.valueOf(999999.00), "USD",
            "Exorbitant transfer", "US", "US", "127.0.0.1", "fp-test-2",
            null
        );

        TransferService.TransferResponse resp = transferService.executeTransfer(idempotencyKey, req);

        assertEquals(PaymentState.REJECTED, resp.state());
        assertTrue(resp.message().contains("Insufficient funds"));

        // Balances must remain unchanged
        Account sender = accountRepo.findById(SENDER_ID).orElseThrow();
        assertEquals(new BigDecimal("10000.00"), sender.getBalance());
    }

    @Test
    @DisplayName("Test 3: Redis Idempotency prevents double-charge on duplicate requests")
    void testIdempotencyPreventsDoubleCharge() {
        Mockito.when(hyperRouteClient.screenTransfer(anyString(), anyDouble(), anyString(), anyString(), anyString()))
            .thenReturn(new HyperRouteClient.ComplianceDecision("CLEAR_TRANSACTION", "CLOSED_HEALTHY", 2, 9, "Cleared"));

        String idempotencyKey = "key-repeat-" + UUID.randomUUID();
        TransferService.TransferRequest req = new TransferService.TransferRequest(
            SENDER_ID, RECEIVER_ID, BigDecimal.valueOf(200.00), "USD",
            "Subscription renewal", "US", "US", "127.0.0.1", "fp-test-3",
            null
        );

        // First call
        TransferService.TransferResponse resp1 = transferService.executeTransfer(idempotencyKey, req);
        assertEquals(PaymentState.SETTLED, resp1.state());

        // Second call with same idempotency key (simulating user double-tap)
        TransferService.TransferResponse resp2 = transferService.executeTransfer(idempotencyKey, req);
        assertTrue(resp2.message().contains("IDEMPOTENT_DUPLICATE"));

        // Verify account was debited EXACTLY once ($10,000 - $200 = $9,800), not twice ($9,600)
        Account sender = accountRepo.findById(SENDER_ID).orElseThrow();
        assertEquals(new BigDecimal("9800.00"), sender.getBalance());
    }
}
