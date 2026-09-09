package com.apexgateway.gateway.controller;

import com.apexgateway.gateway.model.AlertIngestRequest;
import com.apexgateway.gateway.model.AlertIngestResponse;
import com.apexgateway.gateway.service.AgentInvestigationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/gateway")
public class GatewayIngressController {

    private final AgentInvestigationService investigationService;

    public GatewayIngressController(AgentInvestigationService investigationService) {
        this.investigationService = investigationService;
    }

    @PostMapping("/alerts")
    public Mono<ResponseEntity<AlertIngestResponse>> ingestAlert(@RequestBody AlertIngestRequest request) {
        long startTime = System.currentTimeMillis();

        AlertIngestRequest populatedRequest = request.workflowId() == null ? new AlertIngestRequest(
                request.accountId(),
                request.amountUsd(),
                request.senderCountry(),
                request.receiverCountry(),
                request.narrative(),
                "gw-" + UUID.randomUUID().toString().substring(0, 8)) : request;

        return investigationService.dispatchInvestigation(populatedRequest, startTime)
                .map(ResponseEntity::ok);
    }
}