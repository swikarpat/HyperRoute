from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    state: str
    allowed_transitions: list[str] = Field(default_factory=list)
    action: str


class AgentDSLSpec(BaseModel):
    agent_name: str
    allowed_tools: list[str] = Field(default_factory=list)
    max_token_budget: int = Field(gt=0)
    steps: list[AgentStep] = Field(min_length=1)


class AgentDSLCompiler:
    def compile_yaml_to_fsm(self, yaml_content: str) -> dict[str, Any]:
        raw = yaml.safe_load(yaml_content)
        spec = AgentDSLSpec.model_validate(raw)
        states = {step.state: {"action": step.action, "allowed_transitions": step.allowed_transitions} for step in spec.steps}
        unknown = {target for step in spec.steps for target in step.allowed_transitions if target not in states}
        if unknown:
            raise ValueError(f"Transitions reference unknown states: {sorted(unknown)}")
        return {"agent_name": spec.agent_name, "allowed_tools": spec.allowed_tools, "max_token_budget": spec.max_token_budget, "states": states, "start_state": spec.steps[0].state}

    def profile_complexity(self, compiled_fsm: dict[str, Any]) -> int:
        states = compiled_fsm.get("states", {})
        state_score = len(states)
        deep_action_score = sum(1 for value in states.values() if len(value.get("action", "").split()) >= 4 or len(value.get("action", "")) >= 32)
        graph_depth = self._graph_depth(compiled_fsm.get("start_state"), states)
        return state_score + deep_action_score + graph_depth

    @staticmethod
    def _graph_depth(start: str | None, states: dict[str, dict]) -> int:
        def visit(state: str, path: set[str]) -> int:
            if state in path or state not in states:
                return 0
            return 1 + max((visit(target, path | {state}) for target in states[state].get("allowed_transitions", [])), default=0)

        return visit(start, set()) if start else 0


class ModelRouter:
    def __init__(self, complexity_threshold: int = 5, memory_usage: float = 0.0) -> None:
        self.complexity_threshold = complexity_threshold
        self.memory_usage = memory_usage

    def route(self, complexity: int, memory_usage: float | None = None) -> str:
        usage = self.memory_usage if memory_usage is None else memory_usage
        return "local_slm" if complexity < self.complexity_threshold and usage < 0.8 else "heavy_cloud_reasoning_model"