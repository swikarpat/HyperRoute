"""Specialized Google ADK Investigation Agents upgraded with cognitive reasoning and memory."""

from __future__ import annotations

from typing import Any, Dict
from src.google_adk.agents import Agent, AgentContext, Message
from src.google_adk.common.types import AgentTask
from src.google_adk.reasoning import cognitive_engine
from src.google_adk.tools import (
    search_adverse_media,
    traverse_beneficial_ownership_graph,
    query_account_velocity,
    dispatch_enterprise_escalation,
)
from src.memory.memory_store import memory_store


class EntityDisambiguationAgent(Agent):
    """Google ADK Agent for entity resolution, nominee detection, and graph traversal."""

    def __init__(self, **kwargs):
        super().__init__(name="EntityDisambiguationAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        alert = task.data.get("alert", {})
        features = task.data.get("features", [])

        # Cognitive entity evaluation
        findings = cognitive_engine.evaluate_entity(alert, features)

        # Grounding: If high risk, augment with Graph RAG traversal
        if findings.get("shell_company_risk") == "HIGH":
            account_id = alert.get("account_id", "")
            graph_results = traverse_beneficial_ownership_graph(account_id, max_hops=4)
            findings["graph_rag_paths"] = graph_results.get("paths", [])
            findings["nominee_ring_detected"] = graph_results.get("nominee_ring_detected", True)

        # Record into working memory
        memory_store.update_working_state(entity_findings=findings)

        return Message(sender=self.name, data=findings)


class SanctionsComplianceAgent(Agent):
    """Google ADK Agent for OFAC watchlist, PEP screening, and regulatory compliance."""

    def __init__(self, **kwargs):
        super().__init__(name="SanctionsComplianceAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        alert = task.data.get("alert", {})
        features = task.data.get("features", [])

        findings = cognitive_engine.evaluate_sanctions(alert, features)

        # Grounding: Cross-border alerts run adverse media screening
        sender = alert.get("sender_country", "US")
        receiver = alert.get("receiver_country", "US")
        if sender != receiver:
            media = search_adverse_media(alert.get("account_id", ""), sender)
            findings["adverse_media"] = media

        memory_store.update_working_state(sanctions_findings=findings)

        return Message(sender=self.name, data=findings)


class ForensicSynthesisAgent(Agent):
    """Google ADK Agent for forensic narrative synthesis, SAR generation, and FSM proposal."""

    def __init__(self, **kwargs):
        super().__init__(name="ForensicSynthesisAgent", **kwargs)

    async def run(self, context: AgentContext, task: AgentTask) -> Message:
        alert = task.data.get("alert", {})
        account_id = alert.get("account_id", "")

        entity_msg = task.data.get("context_EntityDisambiguationAgent")
        sanctions_msg = task.data.get("context_SanctionsComplianceAgent")

        entity_findings = entity_msg.data if entity_msg else {}
        sanctions_findings = sanctions_msg.data if sanctions_msg else {}

        # Semantic Memory: Recall relevant typologies matching the narrative
        narrative = alert.get("narrative", "")
        matched_typologies = memory_store.recall_typologies(narrative, threshold=0.50, limit=2)

        # Long-Term Memory: Pull prior entity case records
        prior_cases = memory_store.query_entity_history(account_id, limit=3)

        # Cognitive Synthesis
        dossier = cognitive_engine.synthesize_forensic_dossier(
            alert=alert,
            entity_findings=entity_findings,
            sanctions_findings=sanctions_findings,
            typologies=matched_typologies,
            past_cases=prior_cases,
        )

        # Ensure ML risk level from task is preserved
        if task.data.get("ml_risk_level"):
            dossier["risk_level"] = task.data.get("ml_risk_level")

        # Enterprise Escalation if proposed state is 7 (AWAITING_HUMAN_APPROVAL)
        if dossier.get("proposed_fsm_state") == 7:
            escalation = dispatch_enterprise_escalation(
                account_id=account_id,
                amount_usd=alert.get("amount_usd", 0.0),
                narrative=dossier.get("synthesis_narrative", ""),
                fsm_state=7,
            )
            dossier["enterprise_escalation"] = escalation

        return Message(sender=self.name, data=dossier)
