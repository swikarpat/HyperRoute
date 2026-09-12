package com.hyperroute.banking.service;

import com.hyperroute.banking.domain.PaymentState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.*;

/**
 * Traffic Generator & Scenario Simulator for HyperRoute demonstrations.
 * Simulates high-velocity retail, structuring, and large-value cross-border wires.
 */
@Service
public class SimulationService {

    private static final Logger log = LoggerFactory.getLogger(SimulationService.class);

    private final TransferService transferService;

    public record SimulationReport(
        int totalAttempted,
        int settledCount,
        int heldCount,
        int rejectedCount,
        List<TransferService.TransferResponse> results
    ) {}

    public SimulationService(TransferService transferService) {
        this.transferService = transferService;
    }

    public SimulationReport runSimulationBatch(int count, double fraudRatio) {
        log.info("[Simulation] Starting batch simulation: total={}, fraudRatio={}", count, fraudRatio);
        List<TransferService.TransferResponse> results = new ArrayList<>();
        int settled = 0;
        int held = 0;
        int rejected = 0;

        Random random = new Random();

        for (int i = 1; i <= count; i++) {
            boolean isFraudulent = random.nextDouble() < fraudRatio;
            String idempotencyKey = "sim-" + UUID.randomUUID().toString();

            TransferService.TransferRequest req;
            if (isFraudulent) {
                // Generate suspicious scenario (Structuring or sanctioned destination or high-value wire)
                int fraudType = random.nextInt(3);
                if (fraudType == 0) {
                    // Structuring pattern: $9,990 right below $10,000 threshold
                    req = new TransferService.TransferRequest(
                        "ACC-USER-1001", "ACC-MERCHANT-2001",
                        BigDecimal.valueOf(9990.00), "USD",
                        "Cash deposit structuring rapid layering test",
                        "US", "KY", "192.168.1.105", "fp-anon-proxy-88",
                        "{\"pacs008\":{\"amount\":9990.00,\"type\":\"STRUCTURING\"}}"
                    );
                } else if (fraudType == 1) {
                    // Large Wire ($850k)
                    req = new TransferService.TransferRequest(
                        "ACC-CORP-3001", "ACC-MERCHANT-2001",
                        BigDecimal.valueOf(850000.00), "USD",
                        "Offshore corporate acquisition wire",
                        "US", "CH", "10.0.4.15", "fp-corp-treasury",
                        "{\"pacs008\":{\"amount\":850000.00,\"type\":\"HIGH_VALUE_WIRE\"}}"
                    );
                } else {
                    // Sanctioned route
                    req = new TransferService.TransferRequest(
                        "ACC-USER-1001", "ACC-MERCHANT-2001",
                        BigDecimal.valueOf(14500.00), "USD",
                        "International consulting fee to entity in sanctioned list",
                        "US", "IR", "198.51.100.22", "fp-tor-exit",
                        "{\"pacs008\":{\"amount\":14500.00,\"type\":\"SANCTION_RISK\"}}"
                    );
                }
            } else {
                // Nominal benign transfer ($25 to $1,500)
                double nominalAmount = 25.0 + (random.nextDouble() * 1475.0);
                req = new TransferService.TransferRequest(
                    "ACC-USER-1001", "ACC-MERCHANT-2001",
                    BigDecimal.valueOf(nominalAmount).setScale(2, java.math.RoundingMode.HALF_EVEN), "USD",
                    "Grocery checkout purchase ref #" + (1000 + i),
                    "US", "US", "172.16.0.40", "fp-ios-safari",
                    "{\"pacs008\":{\"amount\":" + nominalAmount + ",\"type\":\"RETAIL\"}}"
                );
            }

            TransferService.TransferResponse resp = transferService.executeTransfer(idempotencyKey, req);
            results.add(resp);

            if (resp.state() == PaymentState.SETTLED) {
                settled++;
            } else if (resp.state() == PaymentState.FROZEN) {
                held++;
            } else {
                rejected++;
            }
        }

        log.info("[Simulation] Completed: total={} settled={} held={} rejected={}", count, settled, held, rejected);
        return new SimulationReport(count, settled, held, rejected, results);
    }
}

