package com.apexgateway.gateway.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

public record AlertIngestRequest(
    @JsonProperty("account_id") String accountId,
    @JsonProperty("amount_usd") BigDecimal amountUsd,
    @JsonProperty("sender_country") String senderCountry,
    @JsonProperty("receiver_country") String receiverCountry,
    @JsonProperty("narrative") String narrative,
    @JsonProperty("workflow_id") String workflowId
) {}