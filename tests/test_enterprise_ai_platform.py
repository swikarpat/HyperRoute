import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "agent-runtime"))

from src.a2a.protocol import A2AMessageEnvelope
from src.a2a.supervisor import HandoffBlockedError, MultiAgentSupervisor
from src.compiler.agentscript import AgentDSLCompiler
from src.compiler.router import IntelligentModelRouter
from src.evals.evaluator import EvaluationHarness
from src.mcp.graph_rag import HybridGraphRAG
from src.mcp.server import detect_fincen_structuring, screen_ofac_sanctions
from src.security.token_vault import FinancialTokenVault


class EnterprisePlatformTests(unittest.TestCase):
    def test_token_vault_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = FinancialTokenVault(Path(directory) / "data" / "vault.key")
            original = "SSN 123-45-6789 and Account #123456789"
            redacted, token_map = vault.redact_and_tokenize(original)
            self.assertNotIn("123-45-6789", redacted)
            self.assertEqual(vault.rehydrate(redacted, token_map), original)

    def test_mcp_and_graph_rag(self):
        self.assertTrue(detect_fincen_structuring([9500, 9700])["structuring_detected"])
        self.assertGreater(screen_ofac_sanctions("blocked sanctions entity", "US")["sanctions_match_score"], 0.8)
        graph = HybridGraphRAG()
        graph.add_beneficial_owner("ACC-1", "Nominee-A", "PA")
        graph.add_beneficial_owner("Nominee-A", "Nominee-B", "VG")
        graph.add_beneficial_owner("Nominee-B", "Nominee-C", "KY")
        result = graph.traverse_ownership("ACC-1", 4)
        self.assertTrue(result["nominee_ring_detected"])
        self.assertTrue(any(path[-1]["to"] == "KY" for path in result["paths"]))

    def test_supervisor_rejects_low_confidence(self):
        envelope = A2AMessageEnvelope(sender_agent_id="a", recipient_agent_id="b", intent_capability="review", payload_data={}, confidence_score=0.5, task_id="task")
        with self.assertRaises(HandoffBlockedError):
            MultiAgentSupervisor().evaluate_handoff(envelope)

    def test_compiler_and_router(self):
        compiled = AgentDSLCompiler().compile_yaml_to_fsm("""
agent_name: compliance
allowed_tools: [screen]
max_token_budget: 1000
steps:
  - state: start
    allowed_transitions: [finish]
    action: screen entity
  - state: finish
    allowed_transitions: []
    action: record decision
""")
        self.assertEqual(compiled["start_state"], "start")
        self.assertEqual(IntelligentModelRouter().route(3), "llama3.1:8b")
        self.assertEqual(IntelligentModelRouter().route(5), "claude-3-5-sonnet")
        self.assertEqual(IntelligentModelRouter.compress_prompt("a\n\n b"), "a b")

    def test_evaluation_scorecard_generation(self):
        harness = EvaluationHarness()
        scorecard = harness.evaluate(lambda case: {"decision": case["expected_decision"], "evidence_refs": ["gold-1"]})
        with tempfile.TemporaryDirectory() as directory:
            output = harness.export_markdown(scorecard, Path(directory) / "scorecard.md")
            self.assertTrue(output.exists())
            self.assertIn("Grounding Fidelity", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()