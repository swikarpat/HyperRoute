import pytest

from src.a2a.protocol import A2AMessageEnvelope
from src.a2a.supervisor import HandoffBlockedError, MultiAgentSupervisor
from src.audit.tracer import CryptographicTracer
from src.cache.semantic_cache import SemanticThreatCache
from src.compiler.agentscript import AgentDSLCompiler, ModelRouter
from src.mcp.server import detect_fincen_structuring, screen_ofac_sanctions
from src.security.token_vault import FinancialTokenVault


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