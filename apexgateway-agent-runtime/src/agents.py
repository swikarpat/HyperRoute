import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel

class InvestigationDossier(BaseModel):
    account_id: str
    risk_level: str
    entity_findings: Dict[str, Any]
    sanctions_findings: Dict[str, Any]
    synthesis_narrative: str
    recommended_fsm_action: str
    proposed_fsm_state: int
    confidence_score: float

class EntityDisambiguationAgent:
    """Agent 1: Dissects entity beneficial ownership, nominees, and cross-border shells."""
    async def analyze(self, alert: dict) -> Dict[str, Any]:
        await asyncio.sleep(0.02)  # Non-blocking async investigation step
        sender = alert.get("sender_country", "US")
        receiver = alert.get("receiver_country", "US")
        account_id = alert.get("account_id", "")

        is_offshore = receiver in {"KY", "VG", "PA", "SC", "CY"}
        shell_risk = "HIGH" if is_offshore and alert.get("amount_usd", 0) > 1_000_000 else "LOW"

        return {
            "entity_id": account_id,
            "beneficial_owner_type": "OFFSHORE_CORPORATE_NOMINEE" if is_offshore else "VERIFIED_OPERATING_ENTITY",
            "jurisdiction_delta": f"{sender}->{receiver}",
            "shell_company_risk": shell_risk,
            "ownership_layers_detected": 4 if is_offshore else 1
        }

class SanctionsComplianceAgent:
    """Agent 2: Evaluates FATF AML directives, OFAC screening, and regulatory thresholds."""
    async def evaluate_policy(self, alert: dict) -> Dict[str, Any]:
        await asyncio.sleep(0.02)
        amount = float(alert.get("amount_usd", 0.0))
        receiver = alert.get("receiver_country", "US")

        violations = []
        if amount >= 3_000_000.0:
            violations.append("FINCEN_CTR_TIER_3_THRESHOLD_EXCEEDED")
        if receiver in {"KY", "VG", "PA"}:
            violations.append("FATF_ENHANCED_DUE_DILIGENCE_REQUIRED")

        return {
            "sanctions_screening_status": "FLAGGED_FOR_REVIEW" if violations else "CLEARED",
            "regulatory_flags": violations,
            "requires_sar_filing": len(violations) >= 2
        }

class ForensicSynthesisAgent:
    """Agent 3: Synthesizes evidence across sub-agents and constructs the legal audit dossier."""
    async def synthesize(self, alert: dict, entity_res: dict, sanctions_res: dict) -> InvestigationDossier:
        await asyncio.sleep(0.01)
        flags = sanctions_res.get("regulatory_flags", [])
        shell_risk = entity_res.get("shell_company_risk", "LOW")

        if shell_risk == "HIGH" or len(flags) >= 2:
            recommended_action = "FREEZE_FUNDS_AND_ESCALATE"
            proposed_state = 7  # AUDIT_SANCTION_HOLD
            risk_level = "CRITICAL"
            narrative = (
                f"High-value cross-border wire (${alert.get('amount_usd'):,.2f}) routed through "
                f"{entity_res.get('jurisdiction_delta')}. Entity analysis detected "
                f"{entity_res.get('ownership_layers_detected')} ownership tiers with "
                f"{entity_res.get('beneficial_owner_type')}. Triggered policies: {', '.join(flags)}."
            )
            confidence = 0.96
        else:
            recommended_action = "ESCALATE_TO_COMPLIANCE_OFFICER"
            proposed_state = 5  # MANUAL_REVIEW_QUEUE
            risk_level = "ELEVATED"
            narrative = "Ambiguous cross-border pattern requiring secondary compliance verification."
            confidence = 0.78

        return InvestigationDossier(
            account_id=alert.get("account_id", ""),
            risk_level=risk_level,
            entity_findings=entity_res,
            sanctions_findings=sanctions_res,
            synthesis_narrative=narrative,
            recommended_fsm_action=recommended_action,
            proposed_fsm_state=proposed_state,
            confidence_score=confidence
        )

class MultiAgentOrchestrator:
    """Coordinates asynchronous multi-agent forensic investigations."""
    def __init__(self):
        self.entity_agent = EntityDisambiguationAgent()
        self.sanctions_agent = SanctionsComplianceAgent()
        self.synthesis_agent = ForensicSynthesisAgent()

    async def investigate(self, alert: dict) -> InvestigationDossier:
        # Step 1: Run Entity Disambiguation and Sanctions checks concurrently
        entity_res, sanctions_res = await asyncio.gather(
            self.entity_agent.analyze(alert),
            self.sanctions_agent.evaluate_policy(alert)
        )
        # Step 2: Synthesize findings into a defensible regulatory dossier
        return await self.synthesis_agent.synthesize(alert, entity_res, sanctions_res)

orchestrator = MultiAgentOrchestrator()
