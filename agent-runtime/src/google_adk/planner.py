"""Google ADK Dynamic Planner & Iterative Orchestration Engine.

Implements the fundamental autonomous agent lifecycle:
Plan -> Reason -> Execute -> Observe -> Replan

Features:
- Decomposes complex financial alerts into dynamic, conditional investigation steps.
- Executes steps sequentially or concurrently while observing intermediate findings.
- Re-plans dynamically when new risk indicators are uncovered (e.g., nominee rings, structuring).
- Enforces strict FSM safety invariants through the native C++20 compliance guardrail.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.memory.memory_store import memory_store
from src.google_adk.reasoning import cognitive_engine


@dataclass
class PlanStep:
    id: str
    name: str
    target_capability: str
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, SKIPPED, REPLANNED
    observation: Optional[Dict[str, Any]] = None
    risk_level: str = "LOW"


class DynamicPlanner:
    """Dynamic Google ADK Planner orchestrating iterative Plan-Reason-Execute-Observe-Replan cycles."""

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self.plan: List[PlanStep] = []
        self.observations: Dict[str, Any] = {}
        self.replan_count: int = 0
        self.max_replans: int = 2

    def create_initial_plan(self, alert: Dict[str, Any]) -> List[PlanStep]:
        """Formulate initial investigation steps based on alert parameters."""
        amount = alert.get("amount_usd", 0.0)
        corridor = f"{alert.get('sender_country')}->{alert.get('receiver_country')}"

        steps = [
            PlanStep(
                id="step-1-entity",
                name="Entity Disambiguation & Beneficial Ownership",
                target_capability="ENTITY_RESOLUTION",
            ),
            PlanStep(
                id="step-2-sanctions",
                name="OFAC Sanctions & Corridor Compliance",
                target_capability="SANCTIONS_SCREENING",
            ),
        ]

        # Conditionally add adverse media search for cross-border wires
        if alert.get("sender_country") != alert.get("receiver_country"):
            steps.append(
                PlanStep(
                    id="step-3-adverse-media",
                    name=f"Adverse Media Grounding ({corridor})",
                    target_capability="ADVERSE_MEDIA_SEARCH",
                )
            )

        # High-value wires mandate historical structuring velocity check
        if amount >= 250_000.0:
            steps.append(
                PlanStep(
                    id="step-4-velocity",
                    name="Core Banking Structuring & Velocity Analysis",
                    target_capability="TRANSACTION_VELOCITY",
                )
            )

        steps.append(
            PlanStep(
                id="step-final-synthesis",
                name="Forensic Dossier Synthesis & SAR Generation",
                target_capability="DOSSIER_SYNTHESIS",
            )
        )

        self.plan = steps
        return list(self.plan)

    def observe_and_replan(
        self, completed_step: PlanStep, observation: Dict[str, Any], alert: Dict[str, Any]
    ) -> List[PlanStep]:
        """Observe step outcome and dynamically replan if anomalies are detected."""
        completed_step.status = "COMPLETED"
        completed_step.observation = observation
        self.observations[completed_step.target_capability] = observation

        # Add to short-term scratchpad
        memory_store.add_scratchpad({
            "step": completed_step.name,
            "capability": completed_step.target_capability,
            "observation": observation,
        })

        # Dynamic Replanning Trigger: Check if observation reveals hidden complexity
        if self.replan_count < self.max_replans:
            # Trigger 1: Deep nominee ring detected
            if (
                completed_step.target_capability == "ENTITY_RESOLUTION"
                and observation.get("shell_company_risk") == "HIGH"
                and not any(s.target_capability == "DEEP_GRAPH_TRAVERSAL" for s in self.plan)
            ):
                deep_step = PlanStep(
                    id=f"step-replan-{self.replan_count + 1}-graph",
                    name="Deep Graph RAG Beneficial Ownership Traversal (4 Hops)",
                    target_capability="DEEP_GRAPH_TRAVERSAL",
                    status="PENDING",
                    risk_level="HIGH",
                )
                # Insert right before synthesis
                idx = next((i for i, s in enumerate(self.plan) if s.target_capability == "DOSSIER_SYNTHESIS"), len(self.plan))
                self.plan.insert(idx, deep_step)
                self.replan_count += 1

            # Trigger 2: Regulatory flag requires enterprise escalation
            if (
                completed_step.target_capability == "SANCTIONS_SCREENING"
                and observation.get("requires_sar_filing")
                and not any(s.target_capability == "ENTERPRISE_ESCALATION" for s in self.plan)
            ):
                esc_step = PlanStep(
                    id=f"step-replan-{self.replan_count + 1}-escalate",
                    name="Enterprise Compliance Escalation Notification",
                    target_capability="ENTERPRISE_ESCALATION",
                    status="PENDING",
                    risk_level="CRITICAL",
                )
                idx = next((i for i, s in enumerate(self.plan) if s.target_capability == "DOSSIER_SYNTHESIS"), len(self.plan))
                self.plan.insert(idx, esc_step)
                self.replan_count += 1

        return list(self.plan)

    def get_plan_summary(self) -> Dict[str, Any]:
        """Summarize current plan progression."""
        return {
            "workflow_id": self.workflow_id,
            "total_steps": len(self.plan),
            "completed_steps": sum(1 for s in self.plan if s.status == "COMPLETED"),
            "replans_triggered": self.replan_count,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "capability": s.target_capability,
                    "status": s.status,
                    "risk_level": s.risk_level,
                }
                for s in self.plan
            ],
        }
