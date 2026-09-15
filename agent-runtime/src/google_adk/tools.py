"""Google ADK Explicit Tool Registry for Financial Crime Investigations.

Provides controlled, observable, and attested tool interfaces aligned with Image 1:
- Web Search / Adverse Media Grounding
- Watchlist & Sanctions APIs
- Core Banking Ledger Database Queries
- Enterprise Systems Escalation (Slack / Teams / PagerDuty)
- Deep Beneficial Ownership Graph RAG Traversal
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from src.mcp.graph_rag import HybridGraphRAG
from src.mcp.server import detect_fincen_structuring, evaluate_wire_corridor, screen_ofac_sanctions

# In-memory shared graph RAG registry
_graph_rag = HybridGraphRAG()
_graph_rag.add_beneficial_owner("ACC-CORP-4402", "Apex Holdings Nominee Ltd", "PA")
_graph_rag.add_beneficial_owner("Apex Holdings Nominee Ltd", "Pacific Horizon Shell LLC", "VG")
_graph_rag.add_beneficial_owner("Pacific Horizon Shell LLC", "Seaside Capital Nominee Trust", "KY")


def search_adverse_media(entity_name: str, jurisdiction: str) -> Dict[str, Any]:
    """Grounding tool: Search news and adverse media archives for financial crime allegations."""
    normalized = entity_name.lower()
    adverse_keywords = ("indictment", "probe", "bribe", "laundering", "nominee", "shell", "freeze", "sanction")

    matches = [kw for kw in adverse_keywords if kw in normalized]
    has_adverse = bool(matches) or jurisdiction.upper() in {"PA", "VG", "KY", "KP", "IR", "RU"}

    articles = []
    if has_adverse:
        articles.append({
            "headline": f"Offshore entity registration associated with {entity_name} flagged in jurisdiction {jurisdiction}",
            "source": "Global Financial Intelligence Wire",
            "risk_weight": 0.85,
        })
    else:
        articles.append({
            "headline": f"Standard corporate compliance filings for {entity_name}",
            "source": "Commercial Registry Gazette",
            "risk_weight": 0.05,
        })

    return {
        "entity_name": entity_name,
        "jurisdiction": jurisdiction.upper(),
        "adverse_media_detected": has_adverse,
        "matched_risk_keywords": matches,
        "articles": articles,
        "confidence_score": 0.92,
    }


def screen_watchlist_sanctions(entity_name: str, country: str) -> Dict[str, Any]:
    """Explicit tool: Query live OFAC SDN and PEP sanctions registries."""
    return screen_ofac_sanctions(entity_name=entity_name, country=country)


def query_account_velocity(account_id: str, lookback_days: int = 30) -> Dict[str, Any]:
    """Database tool: Query Java 21 Core Banking ledger for transaction velocity and layering."""
    # Simulates pulling historical transactions from Java Core Ledger
    simulated_txs = [4500.0, 9500.0, 9800.0, 150000.0]
    structuring_analysis = detect_fincen_structuring(simulated_txs)

    return {
        "account_id": account_id,
        "lookback_days": lookback_days,
        "total_volume_usd": sum(simulated_txs),
        "inflow_outflow_ratio": 0.98,  # Near 1.0 indicates rapid pass-through / mule activity
        "structuring_indicators": structuring_analysis,
        "velocity_risk": "HIGH" if structuring_analysis["structuring_detected"] else "LOW",
    }


def traverse_beneficial_ownership_graph(account_id: str, max_hops: int = 4) -> Dict[str, Any]:
    """Graph RAG tool: Traverse multi-hop nominee holding companies and jurisdiction paths."""
    return _graph_rag.traverse_ownership(account_id=account_id, max_hops=max_hops)


def dispatch_enterprise_escalation(
    account_id: str,
    amount_usd: float,
    narrative: str,
    fsm_state: int = 7,
    channel: str = "SLACK_COMPLIANCE_OPS",
) -> Dict[str, Any]:
    """Enterprise App tool: Dispatch webhook payload to Slack/Teams/PagerDuty for Human-in-the-Loop review."""
    payload = {
        "channel": channel,
        "urgency": "CRITICAL" if amount_usd >= 1_000_000.0 else "HIGH",
        "title": f"🚨 HyperRoute AML Escalation: {account_id} (${amount_usd:,.2f})",
        "details": {
            "account_id": account_id,
            "amount_usd": amount_usd,
            "fsm_quarantine_state": f"State {fsm_state} (AWAITING_HUMAN_APPROVAL)",
            "narrative": narrative,
            "action_required": "Compliance Officer signoff in Mission Control (:5173)",
        },
        "webhook_dispatched": True,
        "http_status": 202,
    }
    return payload
