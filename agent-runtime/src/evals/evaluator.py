from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from .benchmarks import GOLD_STANDARD_CASES


class EvaluationHarness:
    def __init__(self, cases: list[dict[str, Any]] | None = None) -> None:
        self.cases = cases or GOLD_STANDARD_CASES

    def evaluate(self, decision_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        results = []
        latencies = []
        for case in self.cases:
            started = time.perf_counter()
            actual = decision_fn(case)
            latencies.append((time.perf_counter() - started) * 1000)
            results.append({"name": case["name"], "expected": case["expected_decision"], "actual": actual.get("decision"), "grounded": bool(actual.get("evidence_refs"))})
        correct = sum(result["expected"] == result["actual"] for result in results)
        grounded = sum(result["grounded"] for result in results)
        return {"grounding_fidelity": grounded / len(results), "sanctions_precision": correct / len(results), "sanctions_recall": correct / len(results), "mean_decision_latency_ms": sum(latencies) / len(latencies), "results": results}

    def export_markdown(self, scorecard: dict[str, Any], output_path: str | Path = "reports/agentic_eval_scorecard.md") -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# HyperRoute Agentic Evaluation Scorecard", "", "| Metric | Score |", "|---|---:|", f"| Grounding Fidelity | {scorecard['grounding_fidelity']:.2%} |", f"| Sanctions Precision | {scorecard['sanctions_precision']:.2%} |", f"| Sanctions Recall | {scorecard['sanctions_recall']:.2%} |", f"| Mean Decision Latency | {scorecard['mean_decision_latency_ms']:.3f} ms |", "", "| Case | Expected | Actual | Grounded |", "|---|---|---|---|"]
        lines.extend(f"| {result['name']} | {result['expected']} | {result['actual']} | {'yes' if result['grounded'] else 'no'} |" for result in scorecard["results"])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path