from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class AgentTask:
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowResult:
    output: Any
