import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "agent-runtime"))

from src.a2a.protocol import A2AMessageEnvelope
from src.a2a.supervisor import HandoffBlockedError, MultiAgentSupervisor
from src.audit.tracer import CryptographicTracer
from src.cache.semantic_cache import SemanticThreatCache
from src.compiler.agentscript import AgentDSLCompiler, ModelRouter
from src.mcp.server import detect_fincen_structuring, screen_ofac_sanctions
from src.security.token_vault import FinancialTokenVault
from src.memory.memory_store import HierarchicalMemoryStore
from src.google_adk.planner import DynamicPlanner
from src.google_adk.tools import (
    search_adverse_media,
    query_account_velocity,
    traverse_beneficial_ownership_graph,
    dispatch_enterprise_escalation,
)
from src.google_adk.reasoning import cognitive_engine


def test_token_vault_redacts_encrypts_and_rehydrates(tmp_path):
    vault = FinancialTokenVault(tmp_path / "data" / "vault.key")
    text = "SSN 123-45-6789, card 4111 1111 1111 1111, Account #123456789, SWIFT DEUTDEFF."
    redacted, token_map = vault.redact_and_tokenize(text)
    assert "123-45-6789" not in redacted
    assert "[SSN_0]" in redacted and "[PAN_0]" in redacted
    assert vault.rehydrate(redacted, token_map) == text
    assert vault.decrypt(token_map["values"]["[SSN_0]"]) == "123-45-6789"


def test_mcp_financial_tools_execute():
    assert screen_ofac_sanctions("Blocked Entity", "US")["sanctions_match_score"] > 0.8
    assert detect_fincen_structuring([9500, 9700])["structuring_detected"] is True


def test_supervisor_blocks_low_confidence_handoff():
    envelope = A2AMessageEnvelope(sender_agent_id="a", recipient_agent_id="b", intent_capability="screen", payload_data={}, confidence_score=0.84, task_id="t")
    supervisor = MultiAgentSupervisor()
    with pytest.raises(HandoffBlockedError, match="blocked"):
        supervisor.evaluate_handoff(envelope)
    assert supervisor.block_events[0]["event"] == "anti_amplification_block"


def test_agentscript_compilation_and_complexity():
    compiled = AgentDSLCompiler().compile_yaml_to_fsm("""
agent_name: investigator
allowed_tools: [screen_ofac_sanctions]
max_token_budget: 2000
steps:
  - state: start
    allowed_transitions: [review]
    action: screen entity
  - state: review
    allowed_transitions: []
    action: trace beneficial ownership deeply
""")
    complexity = AgentDSLCompiler().profile_complexity(compiled)
    assert compiled["start_state"] == "start"
    assert complexity >= 5
    assert ModelRouter().route(complexity) == "heavy_cloud_reasoning_model"


def test_cryptographic_audit_chain_detects_tampering():
    tracer = CryptographicTracer()
    tracer.trace("exec-1", "agent", "screen", {"account": "A"}, timestamp="2026-01-01T00:00:00+00:00")
    tracer.trace("exec-1", "agent", "review", {"risk": 0.9}, timestamp="2026-01-01T00:00:01+00:00")
    assert tracer.verify_chain_integrity()
    tracer.records[0]["action"] = "altered"
    assert not tracer.verify_chain_integrity()


def test_semantic_cache_short_circuits_repeat_narrative():
    cache = SemanticThreatCache()
    cache.put("urgent wire transfer routed through nominee company", {"risk": "high"})
    assert cache.get("urgent wire transfer routed through nominee company") == {"risk": "high"}


def test_four_tier_memory_subsystem_persistence_and_typologies(tmp_path):
    db_file = str(tmp_path / "test_case_history.db")
    mem = HierarchicalMemoryStore(db_path=db_file)

    # 1. Short-term Scratchpad
    mem.add_scratchpad({"step": "1", "data": "trace_detected"})
    assert len(mem.get_scratchpad()) == 1

    # 2. Long-term Persistent SQLite
    mem.save_case(
        case_id="CASE-101",
        account_id="ACC-TEST-99",
        amount_usd=750000.0,
        sender_country="PA",
        receiver_country="US",
        status="ESCALATED_TO_HUMAN",
        fsm_state=7,
        risk_score=0.92,
        narrative="Suspicious structuring through Panama holding company",
        dossier={"risk": "CRITICAL"},
    )
    loaded = mem.get_case("CASE-101")
    assert loaded is not None
    assert loaded["account_id"] == "ACC-TEST-99"
    assert loaded["amount_usd"] == 750000.0
    assert loaded["fsm_state"] == 7

    # 3. Semantic Memory Typologies
    recalled = mem.recall_typologies("structuring deposits under $10,000 threshold", threshold=0.40)
    assert len(recalled) > 0
    assert any("Structuring" in r["name"] for r in recalled)

    # 4. User Preferences
    mem.set_user_preference("officer_42", {"risk_tolerance": "ultra_conservative", "approval_limit": 250000.0})
    prefs = mem.get_user_preference("officer_42")
    assert prefs["risk_tolerance"] == "ultra_conservative"
    assert prefs["approval_limit"] == 250000.0


def test_google_adk_dynamic_planner_replanning_cycle():
    planner = DynamicPlanner(workflow_id="CASE-PLAN-01")
    alert = {
        "account_id": "ACC-CORP-4402",
        "amount_usd": 3400000.0,
        "sender_country": "SG",
        "receiver_country": "US",
        "narrative": "Urgent multi-entity liquidity transfer.",
    }

    # Step 1: Initial plan creation
    initial_steps = planner.create_initial_plan(alert)
    assert len(initial_steps) >= 4

    # Step 2: Observe nominee shell risk -> Dynamic Replanning should insert Deep Graph Traversal!
    entity_step = next(s for s in initial_steps if s.target_capability == "ENTITY_RESOLUTION")
    planner.observe_and_replan(
        completed_step=entity_step,
        observation={"shell_company_risk": "HIGH", "ownership_layers_detected": 4},
        alert=alert,
    )

    assert planner.replan_count == 1
    has_deep_graph = any(s.target_capability == "DEEP_GRAPH_TRAVERSAL" for s in planner.plan)
    assert has_deep_graph is True


def test_google_adk_tools_suite():
    # Adverse Media Grounding
    media = search_adverse_media("Apex Offshore Holding", "PA")
    assert media["adverse_media_detected"] is True
    assert len(media["articles"]) > 0

    # Core Banking Ledger Velocity
    velocity = query_account_velocity("ACC-CORP-4402")
    assert velocity["inflow_outflow_ratio"] > 0.9
    assert "structuring_indicators" in velocity

    # Graph RAG Beneficial Ownership Traversal
    graph = traverse_beneficial_ownership_graph("ACC-CORP-4402", max_hops=4)
    assert graph["nominee_ring_detected"] is True

    # Enterprise Escalation Dispatched
    dispatch = dispatch_enterprise_escalation("ACC-CORP-4402", 3400000.0, "High risk wire", fsm_state=7)
    assert dispatch["webhook_dispatched"] is True
    assert dispatch["urgency"] == "CRITICAL"


def test_cognitive_engine_forensic_synthesis_and_chat_interrogation():
    alert = {
        "account_id": "ACC-CORP-4402",
        "amount_usd": 3400000.0,
        "sender_country": "SG",
        "receiver_country": "US",
        "narrative": "Multi-tier corporate liquidity transfer.",
    }

    entity_findings = {
        "entity_id": "ACC-CORP-4402",
        "beneficial_owner_type": "OFFSHORE_CORPORATE_NOMINEE",
        "shell_company_risk": "HIGH",
        "ownership_layers_detected": 4,
    }

    sanctions_findings = {
        "regulatory_flags": ["FATF_ENHANCED_DUE_DILIGENCE_REQUIRED"],
        "requires_sar_filing": True,
    }

    dossier = cognitive_engine.synthesize_forensic_dossier(
        alert=alert,
        entity_findings=entity_findings,
        sanctions_findings=sanctions_findings,
    )

    assert dossier["recommended_fsm_action"] == "FREEZE_FUNDS_AND_ESCALATE"
    assert dossier["proposed_fsm_state"] == 7
    assert dossier["sar_draft"] is not None
    assert "nominee" in dossier["synthesis_narrative"].lower()

    # Test Interactive Copilot Interrogation
    reply = cognitive_engine.chat_interrogate(
        query="Why was this transaction escalated to human approval?",
        active_alert=alert,
        dossier=dossier,
    )
    assert "State 7" in reply or "AWAITING_HUMAN_APPROVAL" in reply or "escalat" in reply.lower()