package com.hyperroute.banking.domain;

/**
 * Compile-time exhaustive payment states representing the regulatory financial lifecycle.
 */
public enum PaymentState {
    INITIATED,
    PENDING_COMPLIANCE,
    SETTLED,
    FROZEN,
    REJECTED
}
