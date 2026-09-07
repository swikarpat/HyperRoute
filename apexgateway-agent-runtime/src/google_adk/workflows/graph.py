import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any
from src.google_adk.agents import Agent, AgentContext, Message
from src.google_adk.common.types import AgentTask, WorkflowResult

@dataclass
class Node:
    id: str
    agent: Agent

@dataclass
class Edge:
    source: str
    target: str
    context_key: str = ""

class GraphWorkflow:
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_nodes(self, nodes: List[Node]):
        for n in nodes:
            self.nodes[n.id] = n

    def add_edges(self, edges: List[Edge]):
        self.edges.extend(edges)

    async def setup(self):
        pass

    async def shutdown(self):
        pass

    async def run(self, task: AgentTask) -> WorkflowResult:
        context = AgentContext()
        entity_task = AgentTask(data=dict(task.data))
        sanctions_task = AgentTask(data=dict(task.data))

        entity_res = await self.nodes["EntityAnalysis"].agent.run(context, entity_task)
        sanctions_res = await self.nodes["SanctionsScreening"].agent.run(context, sanctions_task)

        synthesis_data = dict(task.data)
        synthesis_data["context_EntityDisambiguationAgent"] = entity_res
        synthesis_data["context_SanctionsComplianceAgent"] = sanctions_res
        synthesis_task = AgentTask(data=synthesis_data)

        synthesis_res = await self.nodes["ForensicSynthesis"].agent.run(context, synthesis_task)

        queue = asyncio.Queue()
        await queue.put(synthesis_res)
        return WorkflowResult(output=queue)
