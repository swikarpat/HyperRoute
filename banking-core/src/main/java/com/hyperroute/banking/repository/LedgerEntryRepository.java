package com.hyperroute.banking.repository;

import com.hyperroute.banking.domain.LedgerEntry;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LedgerEntryRepository extends JpaRepository<LedgerEntry, String> {
    List<LedgerEntry> findByAccountIdOrderByCreatedAtDesc(String accountId);
    List<LedgerEntry> findByTransactionId(String transactionId);
}
