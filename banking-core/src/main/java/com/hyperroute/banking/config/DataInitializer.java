package com.hyperroute.banking.config;

import com.hyperroute.banking.domain.Account;
import com.hyperroute.banking.repository.AccountRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.math.BigDecimal;

@Configuration
public class DataInitializer {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    @Bean
    CommandLineRunner initDatabase(AccountRepository accountRepo) {
        return args -> {
            if (accountRepo.count() == 0) {
                log.info("[DataInit] Seeding initial banking ledger accounts...");

                accountRepo.save(new Account(
                    "ACC-USER-1001", "1001-4492-001", "Alice M. Carter (Retail)",
                    BigDecimal.valueOf(50000.00), "USD", "ACTIVE"
                ));

                accountRepo.save(new Account(
                    "ACC-MERCHANT-2001", "2001-8831-002", "Apex Global Merchant Services",
                    BigDecimal.valueOf(100000.00), "USD", "ACTIVE"
                ));

                accountRepo.save(new Account(
                    "ACC-CORP-3001", "3001-9912-003", "Starlight Treasury Holdings LLC",
                    BigDecimal.valueOf(5000000.00), "USD", "ACTIVE"
                ));

                accountRepo.save(new Account(
                    "ACC-ESCROW-HOLD", "9999-ESCROW-004", "HyperRoute Compliance Escrow Reserve",
                    BigDecimal.ZERO, "USD", "ESCROW_SYSTEM"
                ));

                log.info("[DataInit] Seeded 4 ledger accounts successfully.");
            }
        };
    }
}
