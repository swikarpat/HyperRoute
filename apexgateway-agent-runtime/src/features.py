import math
import re
from typing import List, Dict

HIGH_RISK_JURISDICTIONS = {"AE", "KY", "PA", "VG", "SC", "CY", "MT"}
OFFSHORE_CORRIDORS = {("SG", "KY"), ("US", "VG"), ("HK", "PA"), ("GB", "SC")}

SUSPICIOUS_KEYWORDS = {
    "urgent", "liquidity", "rebalancing", "confidential", "escrow",
    "unallocated", "settlement", "nominee", "structuring", "intermediary"
}

def extract_features(alert: dict) -> List[float]:
    """
    Extracts a 10-dimensional normalized feature vector for statistical inference:
    0: Normalized log amount
    1: Cross-border indicator (0.0 or 1.0)
    2: High-risk sender jurisdiction (0.0 or 1.0)
    3: High-risk receiver jurisdiction (0.0 or 1.0)
    4: Known offshore routing corridor (0.0 or 1.0)
    5: Round-number structuring indicator ($9,500 - $9,999 or clean millions)
    6: High-velocity synthetic account risk
    7: High-value corporate threshold (> $1M USD)
    8: Suspicious narrative keyword density
    9: Geographic risk differential
    """
    amount = float(alert.get("amount_usd", 0.0))
    sender = alert.get("sender_country", "US").upper()
    receiver = alert.get("receiver_country", "US").upper()
    narrative = alert.get("narrative", "").lower()

    # Feature 0: Log-scaled amount
    norm_log_amount = min(math.log10(max(amount, 1.0)) / 8.0, 1.0)

    # Feature 1: Cross border
    is_cross_border = 1.0 if sender != receiver else 0.0

    # Feature 2 & 3: High risk jurisdictions
    hr_sender = 1.0 if sender in HIGH_RISK_JURISDICTIONS else 0.0
    hr_receiver = 1.0 if receiver in HIGH_RISK_JURISDICTIONS else 0.0

    # Feature 4: Offshore corridor
    is_offshore_corridor = 1.0 if (sender, receiver) in OFFSHORE_CORRIDORS else 0.0

    # Feature 5: Structuring indicator (just under reporting thresholds)
    is_structuring = 1.0 if (9000 <= amount < 10000) or (amount > 100000 and amount % 100000 == 0) else 0.0

    # Feature 6: Account velocity proxy (hash parity)
    account_id = alert.get("account_id", "")
    velocity_proxy = 1.0 if hash(account_id) % 7 == 0 else 0.2

    # Feature 7: High-value threshold
    is_high_value = 1.0 if amount >= 1_000_000.0 else 0.0

    # Feature 8: Suspicious narrative keyword match ratio
    tokens = set(re.findall(r"\b\w+\b", narrative))
    matches = len(tokens.intersection(SUSPICIOUS_KEYWORDS))
    keyword_ratio = min(matches / 3.0, 1.0)

    # Feature 9: Cross-continental routing differential
    geo_diff = 1.0 if is_cross_border and (hr_sender or hr_receiver) else 0.0

    return [
        norm_log_amount,
        is_cross_border,
        hr_sender,
        hr_receiver,
        is_offshore_corridor,
        is_structuring,
        velocity_proxy,
        is_high_value,
        keyword_ratio,
        geo_diff
    ]
