package com.hyperroute.banking.controller;

import com.hyperroute.banking.service.SimulationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/core/simulation")
public class SimulationController {

    private final SimulationService simulationService;

    public SimulationController(SimulationService simulationService) {
        this.simulationService = simulationService;
    }

    /**
     * Triggers a batch simulation of financial transfers to demonstrate real-time fraud detection.
     * @param count Number of transfers to generate (default: 10)
     * @param fraudRatio Ratio of suspicious/structuring/high-value wires (default: 0.20)
     */
    @PostMapping("/stream")
    public ResponseEntity<SimulationService.SimulationReport> streamSimulation(
        @RequestParam(defaultValue = "10") int count,
        @RequestParam(defaultValue = "0.20") double fraudRatio
    ) {
        SimulationService.SimulationReport report = simulationService.runSimulationBatch(count, fraudRatio);
        return ResponseEntity.ok(report);
    }
}
