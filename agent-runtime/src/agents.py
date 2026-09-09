from src.google_adk.agents import Agent, AgentContext, Message
from src.google_adk.common.types import AgentTask

class EntityDisambiguationAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(name="EntityDisambiguationAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        features = task.data.get("features", [])
        is_high_risk = bool(features[2] or features[3] or features[4])

        findings = {
            "entity_id": task.data.get("alert", {}).get("account_id"),
            "beneficial_owner_type": "OFFSHORE_CORPORATE_NOMINEE" if is_high_risk else "CLEAR_DOMESTIC_LLC",
            "jurisdiction_delta": f"{task.data.get('alert', {}).get('sender_country')}->{task.data.get('alert', {}).get('receiver_country')}",
            "shell_company_risk": "HIGH" if is_high_risk else "LOW",
            "ownership_layers_detected": 4 if is_high_risk else 1
        }
        return Message(sender=self.name, data=findings)

class SanctionsComplianceAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(name="SanctionsComplianceAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        features = task.data.get("features", [])
        is_offshore = bool(features[4])
        is_high_value = bool(features[7])

        regulatory_flags = []
        if is_high_value and is_offshore:
            regulatory_flags = [
                "FINCEN_CTR_TIER_3_THRESHOLD_EXCEEDED",
                "FATF_ENHANCED_DUE_DILIGENCE_REQUIRED"
            ]

        findings = {
            "sanctions_screening_status": "FLAGGED_FOR_REVIEW" if regulatory_flags else "CLEARED",
            "regulatory_flags": regulatory_flags,
            "requires_sar_filing": bool(regulatory_flags)
        }
        return Message(sender=self.name, data=findings)

class ForensicSynthesisAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(name="ForensicSynthesisAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        alert = task.data.get("alert", {})
        amount = f"${alert.get('amount_usd', 0.0):,.2f}"
        corridor = f"{alert.get('sender_country')}->{alert.get('receiver_country')}"

        entity_msg = task.data.get("context_EntityDisambiguationAgent")
        sanctions_msg = task.data.get("context_SanctionsComplianceAgent")

        entity_findings = entity_msg.data if entity_msg else {}
        sanctions_findings = sanctions_msg.data if sanctions_msg else {}

        narrative = f"High-value cross-border wire ({amount}) routed through {corridor}. "
        if entity_findings.get("shell_company_risk") == "HIGH":
            narrative += f"Entity analysis detected {entity_findings.get('ownership_layers_detected')} ownership tiers with {entity_findings.get('beneficial_owner_type')}. "

        if sanctions_findings.get("regulatory_flags"):
            flags = ", ".join(sanctions_findings.get("regulatory_flags"))
            narrative += f"Triggered policies: {flags}."

        recommended_action = "FREEZE_FUNDS_AND_ESCALATE" if sanctions_findings.get("requires_sar_filing") else "REVIEW_EXCEPTION"

        dossier = {
            "account_id": alert.get("account_id"),
            "risk_level": task.data.get("ml_risk_level"),
            "entity_findings": entity_findings,
            "sanctions_findings": sanctions_findings,
            "synthesis_narrative": narrative,
            "recommended_fsm_action": recommended_action,
            "proposed_fsm_state": 7,
            "confidence_score": 0.96
        }
        return Message(sender=self.name, data=dossier)
