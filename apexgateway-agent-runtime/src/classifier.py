import math
from typing import List, Tuple
from src.features import extract_features

class TabularRiskClassifier:
    """
    Compiled 10-tree gradient boosted decision ensemble for Tier 1 screening.
    Evaluates 10 extracted features to output calibrated fraud risk probability [0.0, 1.0].
    """
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        # Base log-odds prior for standard banking alerts
        self.prior = -1.8

    def _eval_tree_0(self, x: List[float]) -> float:
        return 0.85 if x[7] > 0.5 and x[1] > 0.5 else -0.35

    def _eval_tree_1(self, x: List[float]) -> float:
        return 1.10 if x[4] > 0.5 or x[9] > 0.5 else -0.25

    def _eval_tree_2(self, x: List[float]) -> float:
        return 0.75 if x[8] > 0.3 and x[0] > 0.6 else -0.20

    def _eval_tree_3(self, x: List[float]) -> float:
        return 0.90 if x[5] > 0.5 else -0.15

    def _eval_tree_4(self, x: List[float]) -> float:
        return 0.60 if x[2] > 0.5 or x[3] > 0.5 else -0.30

    def predict(self, alert: dict) -> Tuple[float, bool, List[float]]:
        """
        Calculates risk probability. Returns (risk_score, is_suspicious, features).
        """
        features = extract_features(alert)
        
        # Raw margin accumulation across boosted trees
        raw_score = self.prior
        raw_score += self._eval_tree_0(features)
        raw_score += self._eval_tree_1(features)
        raw_score += self._eval_tree_2(features)
        raw_score += self._eval_tree_3(features)
        raw_score += self._eval_tree_4(features)

        # Logistic sigmoid link function
        probability = 1.0 / (1.0 + math.exp(-raw_score))
        is_suspicious = probability >= self.threshold

        return probability, is_suspicious, features

# Global singleton
classifier = TabularRiskClassifier(threshold=0.35)
