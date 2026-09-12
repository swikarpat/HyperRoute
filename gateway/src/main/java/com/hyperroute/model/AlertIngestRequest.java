package com.hyperroute.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

@JsonIgnoreProperties(ignoreUnknown = true)
public record AlertIngestRequest(
    @JsonProperty("account_id") String accountId,
    @JsonProperty("amount_usd") BigDecimal amountUsd,
    @JsonProperty("sender_country") String senderCountry,
    @JsonProperty("receiver_country") String receiverCountry,
    @JsonProperty("narrative") String narrative,
    @JsonProperty("workflow_id") String workflowId
) {
    public AlertIngestRequest withWorkflowId(String newWorkflowId) {
        return new AlertIngestRequest(
            this.accountId(),
            this.amountUsd(),
            this.senderCountry(),
            this.receiverCountry(),
            this.narrative(),
            newWorkflowId
        );
    }
}

