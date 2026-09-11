from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any


class SemanticThreatCache:
    def __init__(self, threshold: float = 0.92, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.threshold = threshold
        self.model_name = model_name
        self._entries: list[tuple[str, Any, list[float]]] = []
        self._model = None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
        except (ImportError, OSError):
            self._model = None

    def put(self, narrative: str, result: Any) -> None:
        self._entries.append((narrative, result, self._embedding(narrative)))

    def get(self, narrative: str) -> Any | None:
        query = self._embedding(narrative)
        best = max(((self._cosine(query, embedding), result) for _, result, embedding in self._entries), default=(0.0, None), key=lambda item: item[0])
        return best[1] if best[0] >= self.threshold else None

    def lookup(self, narrative: str) -> Any | None:
        return self.get(narrative)

    def _embedding(self, text: str) -> list[float]:
        if self._model is not None:
            return list(self._model.encode(text, normalize_embeddings=True))
        counts = Counter(re.findall(r"[a-z0-9]+", text.lower()))
        vector = [0.0] * 128
        for token, count in counts.items():
            vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(vector)] += float(count)
        length = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / length for value in vector]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))