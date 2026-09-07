from src.google_adk.workflows.graph import GraphWorkflow, Node, Edge
from src.agents import EntityDisambiguationAgent, SanctionsComplianceAgent, ForensicSynthesisAgent

class ComplianceInvestigationGraph(GraphWorkflow):
    def __init__(self, **kwargs):
        super().__init__(name="ComplianceInvestigationGraph", **kwargs)
        self.entity_agent = EntityDisambiguationAgent()
        self.sanctions_agent = SanctionsComplianceAgent()
        self.synthesis_agent = ForensicSynthesisAgent()

        self.add_nodes([
            Node(id="EntityAnalysis", agent=self.entity_agent),
            Node(id="SanctionsScreening", agent=self.sanctions_agent),
            Node(id="ForensicSynthesis", agent=self.synthesis_agent)
        ])

        self.add_edges([
            Edge(source="START", target="EntityAnalysis"),
            Edge(source="START", target="SanctionsScreening"),
            Edge(source="EntityAnalysis", target="ForensicSynthesis", context_key="context_EntityDisambiguationAgent"),
            Edge(source="SanctionsScreening", target="ForensicSynthesis", context_key="context_SanctionsComplianceAgent"),
            Edge(source="ForensicSynthesis", target="END")
        ])

investigation_graph = ComplianceInvestigationGraph()
