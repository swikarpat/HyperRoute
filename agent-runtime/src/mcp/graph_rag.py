"""Small in-memory hybrid graph/vector retriever for ownership investigations."""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from typing import Any


class HybridGraphRAG:
    def __init__(self) -> None:
        self._edges: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._documents: dict[str, str] = {}

    def add_entity(self, entity_id: str, description: str = "") -> None:
        self._documents[entity_id] = description or entity_id

    def add_relationship(self, source: str, relationship: str, target: str) -> None:
        self.add_entity(source)
        self.add_entity(target)
        self._edges[source].append((relationship, target))

    def add_beneficial_owner(self, entity: str, company: str, jurisdiction: str | None = None) -> None:
        self.add_relationship(entity, "BENEFICIAL_OWNER", company)
        if jurisdiction:
            self.add_relationship(company, "REGISTERED_IN", jurisdiction)

    def traverse_ownership(self, account_id: str, max_hops: int = 4) -> dict[str, Any]:
        hops = max(0, min(int(max_hops), 4))
        paths: list[list[dict[str, str]]] = []

        def walk(node: str, path: list[dict[str, str]], depth: int, visited: set[str]) -> None:
            if depth >= hops:
                if path:
                    paths.append(path)
                return
            outgoing = [(relation, target) for relation, target in self._edges.get(node, []) if target not in visited]
            if not outgoing:
                if path:
                    paths.append(path)
                return
            for relation, target in outgoing:
                walk(target, path + [{"from": node, "relationship": relation, "to": target}], depth + 1, visited | {target})

        walk(account_id, [], 0, {account_id})
        return {"account_id": account_id, "max_hops": hops, "paths": paths, "nominee_ring_detected": any(len(path) >= 3 for path in paths), "similar_entities": self.similar_entities(account_id)}

    def similar_entities(self, query: str, threshold: float = 0.75) -> list[dict[str, Any]]:
        query_vector = self._embed(query)
        matches = []
        for entity_id, description in self._documents.items():
            score = self._cosine(query_vector, self._embed(description))
            if score >= threshold:
                matches.append({"entity_id": entity_id, "similarity": round(score, 4)})
        return sorted(matches, key=lambda item: item["similarity"], reverse=True)

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = [0.0] * 128
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(vector)] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))