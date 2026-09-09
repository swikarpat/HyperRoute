import os
from typing import Dict, Any
from google.adk import Agent, Workflow
from src.fsm_client import FsmEngineClient
from generated.apexgateway.v1 import fsm_engine_pb2 as pb

fsm_client = FsmEngineClient()

# State Enum mapping matching protobuf
IDLE = pb.AGENT_STATE_IDLE
INGESTING_ALERT = pb.AGENT_STATE_INGESTING_ALERT
PARSING_EVIDENCE = pb.AGENT_STATE_PARSING_EVIDENCE
EXTRACTING_ACCOUNTS = pb.AGENT_STATE_EXTRACTING_ACCOUNTS
CORRELATING_HISTORY = pb.AGENT_STATE_CORRELATING_HISTORY
EVALUATING_RISK = pb.AGENT_STATE_EVALUATING_RISK
AWAITING_HUMAN_APPROVAL = pb.AGENT_STATE_AWAITING_HUMAN_APPROVAL
ISSUING_CLEARANCE = pb.AGENT_STATE_ISSUING_CLEARANCE
EXECUTING_FREEZE = pb.AGENT_STATE_EXECUTING_FREEZE


def step_transition(workflow_id: str, agent_name: str, from_s: int, to_s: int, step_idx: int):
    """Enforces that the ADK Agent step is deterministically permitted by the C++ engine."""
    allowed, code, reason, latency_ns = fsm_client.validate_transition(
        workflow_id=workflow_id,
        agent_id=agent_name,
        from_state=from_s,
        to_state=to_s,
        step_index=step_idx,
    )
    if not allowed:
        raise PermissionError(
            f"[FSM Guardrail Intercept] Agent '{agent_name}' transition rejected: {reason} (Code: {code})"
        )
    print(f"  ✓ [C++ FSM Engine] Step {step_idx}: State {from_s} -> {to_s} approved in {latency_ns / 1_000_000:.3f} ms")


class ApexFraudInvestigationADK:
    """Autonomous Financial Crime Investigation pipeline built on Google ADK."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.step_counter = 0

        # ADK Specialized Agents
        self.evidence_agent = Agent(
            name="evidence_parser_agent",
            instruction=(
                "Parse transaction logs, extract financial ledger traces, and isolate source/destination entities."
            )
        )

        self.forensic_agent = Agent(
            name="forensic_account_agent",
            instruction=(
                "Correlate historical account behavior, check watchlists, and calculate transaction layering velocity."
            )
        )

        self.risk_decision_agent = Agent(
            name="risk_decision_agent",
            instruction=(
                "Synthesize composite risk scores. If amount > $500,000, trigger AWAITING_HUMAN_APPROVAL."
            )
        )

    def execute_investigation(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n➔ [ADK Runtime] Starting Investigation for Case: {self.workflow_id}")
        tx_amount = alert_payload.get("amount_usd", 0.0)

        # Step 1: IDLE -> INGESTING_ALERT
        self.step_counter += 1
        step_transition(self.workflow_id, "gateway", IDLE, INGESTING_ALERT, self.step_counter)

        # Step 2: INGESTING_ALERT -> PARSING_EVIDENCE
        self.step_counter += 1
        step_transition(self.workflow_id, self.evidence_agent.name, INGESTING_ALERT, PARSING_EVIDENCE, self.step_counter)

        # Step 3: PARSING_EVIDENCE -> EXTRACTING_ACCOUNTS
        self.step_counter += 1
        step_transition(self.workflow_id, self.forensic_agent.name, PARSING_EVIDENCE, EXTRACTING_ACCOUNTS, self.step_counter)

        # Step 4: EXTRACTING_ACCOUNTS -> CORRELATING_HISTORY
        self.step_counter += 1
        step_transition(self.workflow_id, self.forensic_agent.name, EXTRACTING_ACCOUNTS, CORRELATING_HISTORY, self.step_counter)

        # Step 5: CORRELATING_HISTORY -> EVALUATING_RISK
        self.step_counter += 1
        step_transition(self.workflow_id, self.risk_decision_agent.name, CORRELATING_HISTORY, EVALUATING_RISK, self.step_counter)

        # Step 6: Regulatory Branching Gate
        if tx_amount >= 500_000:
            self.step_counter += 1
            step_transition(self.workflow_id, self.risk_decision_agent.name, EVALUATING_RISK, AWAITING_HUMAN_APPROVAL, self.step_counter)
            status = "ESCALATED_TO_HUMAN"
            final_state = AWAITING_HUMAN_APPROVAL
        else:
            self.step_counter += 1
            step_transition(self.workflow_id, self.risk_decision_agent.name, EVALUATING_RISK, ISSUING_CLEARANCE, self.step_counter)
            status = "AUTOMATIC_CLEARANCE_ISSUED"
            final_state = ISSUING_CLEARANCE

        return {
            "workflow_id": self.workflow_id,
            "status": status,
            "final_fsm_state": final_state,
            "total_steps_executed": self.step_counter,
            "transaction_amount": tx_amount
        }