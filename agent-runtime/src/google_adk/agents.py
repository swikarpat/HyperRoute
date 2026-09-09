from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Message:
    sender: str
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentContext:
    metadata: Dict[str, Any] = field(default_factory=dict)

class Agent:
    def __init__(self, name: str, **kwargs):
        self.name = name

    async def run(self, context: AgentContext, task: Any) -> Message:
        raise NotImplementedError
