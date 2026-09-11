from __future__ import annotations

import re


class IntelligentModelRouter:
    def __init__(self, memory_pressure_limit: float = 0.8) -> None:
        self.memory_pressure_limit = memory_pressure_limit

    def route(self, complexity: int, memory_pressure: float = 0.0) -> str:
        if complexity < 5 and memory_pressure < self.memory_pressure_limit:
            return "llama3.1:8b"
        return "claude-3-5-sonnet"

    @staticmethod
    def compress_prompt(prompt: str) -> str:
        return re.sub(r"\s+", " ", prompt).strip()