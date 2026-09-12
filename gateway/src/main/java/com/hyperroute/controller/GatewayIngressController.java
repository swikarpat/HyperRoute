package com.hyperroute.controller;

import com.hyperroute.model.AlertIngestRequest;
import com.hyperroute.model.AlertIngestResponse;
import com.hyperroute.service.AgentInvestigationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
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

        AlertIngestRequest populatedRequest = request.workflowId() == null || request.workflowId().isBlank()
                ? request.withWorkflowId("gw-" + UUID.randomUUID().toString().substring(0, 8))
                : request;

        return investigationService.dispatchInvestigation(populatedRequest, startTime)
                .map(ResponseEntity::ok);
    }
}

