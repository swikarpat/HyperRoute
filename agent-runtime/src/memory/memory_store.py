"""Three-layer memory for active investigations and historical typologies."""

from __future__ import annotations

import hashlib
import math
import re
from collections import deque
from typing import Any


class HierarchicalMemoryStore:
    def __init__(self, scratchpad_capacity: int = 32, embedding_dimensions: int = 128) -> None:
        if scratchpad_capacity < 1:
            raise ValueError("scratchpad_capacity must be positive")
        self._scratchpad: deque[Any] = deque(maxlen=scratchpad_capacity)
        self._working_state: dict[str, Any] = {}
        self._episodic: list[tuple[str, Any, list[float]]] = []
        self._dimensions = embedding_dimensions

    def add_scratchpad(self, output: Any) -> None:
        self._scratchpad.append(output)

    def get_scratchpad(self) -> list[Any]:
        return list(self._scratchpad)

    def update_working_state(self, **values: Any) -> dict[str, Any]:
        self._working_state.update(values)
        return dict(self._working_state)

    def get_working_state(self) -> dict[str, Any]:
        return dict(self._working_state)

    def remember_episode(self, narrative: str, outcome: Any) -> None:
        self._episodic.append((narrative, outcome, self._embed(narrative)))

    def recall_episodes(self, narrative: str, threshold: float = 0.75, limit: int = 5) -> list[dict[str, Any]]:
        query = self._embed(narrative)
        matches = [
            {"narrative": text, "outcome": outcome, "similarity": self._cosine(query, embedding)}
            for text, outcome, embedding in self._episodic
        ]
        return sorted((match for match in matches if match["similarity"] >= threshold), key=lambda item: item["similarity"], reverse=True)[:limit]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            vector[int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self._dimensions] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))