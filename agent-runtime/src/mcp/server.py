"""Deterministic financial intelligence tools exposed through FastMCP."""

try:
    from fastmcp import FastMCP
except ImportError:
    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, name: str):
            self.name = name
            self.tools = {}

        def tool(self, function):
            self.tools[function.__name__] = function
            return function


mcp = FastMCP("HyperRoute Financial Intelligence Tools")
GREY_LIST = {"AE", "BB", "BF", "GI", "HT", "JM", "JO", "ML", "MZ", "NG", "PA", "PH", "SN", "ZA", "SS", "SY", "TZ", "TR", "UG", "YE"}


@mcp.tool
def screen_ofac_sanctions(entity_name: str, country: str) -> dict:
    normalized = entity_name.strip().lower()
    indicators = ("sanction", "terror", "drug", "blocked")
    score = min(0.99, 0.78 + 0.05 * sum(word in normalized for word in indicators)) if any(word in normalized for word in indicators) else 0.03
    return {"entity_name": entity_name, "country": country.upper(), "sanctions_match_score": round(score, 2), "pep_status": country.upper() in {"KP", "IR", "SY"}}


@mcp.tool
def trace_beneficial_ownership(account_id: str, max_depth: int) -> dict:
    depth = max(0, min(int(max_depth), 10))
    tiers = [f"nominee-tier-{index + 1}" for index in range(depth)]
    return {"account_id": account_id, "corporate_nominee_tiers": tiers, "shell_company_risk": "HIGH" if depth >= 3 else "LOW", "jurisdiction_paths": [["account", f"jurisdiction-{index + 1}"] for index in range(depth)]}


@mcp.tool
def detect_fincen_structuring(transactions: list[float]) -> dict:
    flagged = [amount for amount in transactions if 9_000 <= float(amount) < 10_000]
    return {"structuring_detected": len(flagged) >= 2, "flagged_deposits": flagged, "ctr_threshold_usd": 10_000.0}


@mcp.tool
def evaluate_wire_corridor(sender_country: str, receiver_country: str) -> dict:
    sender, receiver = sender_country.upper(), receiver_country.upper()
    matches = [country for country in (sender, receiver) if country in GREY_LIST]
    risk = min(1.0, 0.2 + 0.35 * len(matches))
    return {"sender_country": sender, "receiver_country": receiver, "fatf_grey_list_matches": matches, "corridor_risk_score": round(risk, 2)}