"""Comprehensive 4-Tier Memory Subsystem for Google ADK Autonomous Agents.

Aligns with production architecture:
1. Short-term memory: Active task scratchpad and working state
2. Long-term memory: Persisted case history, verdicts, and investigator overrides (SQLite backed)
3. Semantic memory: Vectorized fraud typologies and FATF/FinCEN red flag retrieval
4. User preferences: Compliance officer profiles, thresholds, and risk tolerances
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional


class HierarchicalMemoryStore:
    """4-Tier Memory Architecture honoring: Agent State != Memory Storage."""

    def __init__(
        self,
        scratchpad_capacity: int = 32,
        embedding_dimensions: int = 128,
        db_path: Optional[str] = None,
    ) -> None:
        if scratchpad_capacity < 1:
            raise ValueError("scratchpad_capacity must be positive")

        # Tier 1: Short-term Memory (Transient execution scratchpad)
        self._scratchpad: deque[Any] = deque(maxlen=scratchpad_capacity)
        self._working_state: dict[str, Any] = {}

        # Tier 3: Semantic Memory (In-memory vector store for typologies & episodes)
        self._episodic: list[tuple[str, Any, list[float]]] = []
        self._typologies: list[dict[str, Any]] = []
        self._dimensions = embedding_dimensions

        # Tier 4: User Preferences (Compliance officer settings)
        self._user_preferences: dict[str, dict[str, Any]] = {
            "default": {
                "risk_tolerance": "strict",
                "auto_escalate_amount": 500000.0,
                "sar_drafting_style": "fincen_bsa_standard",
                "high_risk_jurisdictions": ["KP", "IR", "SY", "RU", "MM", "YE"],
                "require_dual_approval_over_million": True,
            }
        }

        # Tier 2: Long-term Memory (Persistent Storage)
        if db_path is None:
            base_dir = Path(__file__).resolve().parents[2] / "data" / "memory"
            base_dir.mkdir(parents=True, exist_ok=True)
            self._db_path = str(base_dir / "case_history.db")
        else:
            self._db_path = db_path
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()
        self._seed_default_typologies()

    def _init_db(self) -> None:
        """Initialize SQLite database for persistent long-term case storage."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS case_history (
                    case_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    sender_country TEXT,
                    receiver_country TEXT,
                    status TEXT NOT NULL,
                    fsm_state INTEGER NOT NULL,
                    risk_score REAL,
                    narrative TEXT,
                    dossier_json TEXT,
                    supervisor_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_account_id ON case_history(account_id);
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS officer_preferences (
                    officer_id TEXT PRIMARY KEY,
                    settings_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Tier 1: Short-Term Memory
    # -------------------------------------------------------------------------
    def add_scratchpad(self, output: Any) -> None:
        """Add intermediate step observation to short-term scratchpad."""
        self._scratchpad.append(output)

    def get_scratchpad(self) -> list[Any]:
        """Retrieve short-term scratchpad items."""
        return list(self._scratchpad)

    def clear_scratchpad(self) -> None:
        """Flush short-term scratchpad for new investigation."""
        self._scratchpad.clear()

    def update_working_state(self, **values: Any) -> dict[str, Any]:
        """Update active execution state."""
        self._working_state.update(values)
        return dict(self._working_state)

    def get_working_state(self) -> dict[str, Any]:
        """Get copy of current working state."""
        return dict(self._working_state)

    def reset_working_state(self) -> None:
        """Reset active working state."""
        self._working_state.clear()

    # -------------------------------------------------------------------------
    # Tier 2: Long-Term Memory (Persistent)
    # -------------------------------------------------------------------------
    def save_case(
        self,
        case_id: str,
        account_id: str,
        amount_usd: float,
        sender_country: str,
        receiver_country: str,
        status: str,
        fsm_state: int,
        risk_score: float = 0.0,
        narrative: str = "",
        dossier: Optional[Dict[str, Any]] = None,
        supervisor_notes: Optional[str] = None,
    ) -> None:
        """Persist investigation result to long-term memory."""
        dossier_str = json.dumps(dossier or {})
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO case_history
                (case_id, account_id, amount_usd, sender_country, receiver_country, status, fsm_state, risk_score, narrative, dossier_json, supervisor_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    account_id,
                    amount_usd,
                    sender_country,
                    receiver_country,
                    status,
                    fsm_state,
                    risk_score,
                    narrative,
                    dossier_str,
                    supervisor_notes,
                ),
            )
            conn.commit()

        # Also register in episodic memory for fast similarity recall
        summary = f"Account {account_id}: {narrative} (${amount_usd:,.2f} from {sender_country} to {receiver_country})"
        self.remember_episode(summary, {"status": status, "case_id": case_id, "fsm_state": fsm_state})

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Fetch historical case by ID."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM case_history WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["dossier"] = json.loads(data.pop("dossier_json", "{}"))
            return data

    def query_entity_history(self, account_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve historical cases for a specific entity/account."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM case_history WHERE account_id = ? ORDER BY created_at DESC LIMIT ?",
                (account_id, limit),
            )
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                item["dossier"] = json.loads(item.pop("dossier_json", "{}"))
                results.append(item)
            return results

    def list_recent_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List most recent cases."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT case_id, account_id, amount_usd, status, fsm_state, risk_score, created_at FROM case_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Tier 3: Semantic Memory (Knowledge Base & Typologies)
    # -------------------------------------------------------------------------
    def remember_episode(self, narrative: str, outcome: Any) -> None:
        """Store narrative episode with vector embedding."""
        self._episodic.append((narrative, outcome, self._embed(narrative)))

    def recall_episodes(self, narrative: str, threshold: float = 0.70, limit: int = 5) -> list[dict[str, Any]]:
        """Recall episodes matching query narrative by cosine similarity."""
        query = self._embed(narrative)
        matches = [
            {"narrative": text, "outcome": outcome, "similarity": self._cosine(query, embedding)}
            for text, outcome, embedding in self._episodic
        ]
        return sorted((match for match in matches if match["similarity"] >= threshold), key=lambda item: item["similarity"], reverse=True)[:limit]

    def remember_typology(self, typology_name: str, description: str, category: str, red_flags: list[str]) -> None:
        """Add known AML/Fraud typology with semantic vector."""
        full_text = f"{typology_name} {description} {' '.join(red_flags)}"
        self._typologies.append({
            "name": typology_name,
            "description": description,
            "category": category,
            "red_flags": red_flags,
            "vector": self._embed(full_text),
        })

    def recall_typologies(self, query_text: str, threshold: float = 0.55, limit: int = 3) -> list[dict[str, Any]]:
        """Recall known money laundering typologies semantically matching an alert."""
        query_vec = self._embed(query_text)
        matches = []
        for typ in self._typologies:
            sim = self._cosine(query_vec, typ["vector"])
            if sim >= threshold:
                matches.append({
                    "name": typ["name"],
                    "category": typ["category"],
                    "description": typ["description"],
                    "red_flags": typ["red_flags"],
                    "similarity": round(sim, 3),
                })
        return sorted(matches, key=lambda x: x["similarity"], reverse=True)[:limit]

    def _seed_default_typologies(self) -> None:
        """Seed industry-standard FinCEN & FATF typologies."""
        self.remember_typology(
            typology_name="FinCEN Structuring & Smurfing",
            description="Deliberately structuring wire or cash deposits just under the $10,000 regulatory reporting threshold.",
            category="STRUCTURING",
            red_flags=["Amounts between $9,000 and $9,999", "Rapid sequence of deposits", "Multiple branch routing"],
        )
        self.remember_typology(
            typology_name="Offshore Nominee Layering",
            description="Routing transactions through shell companies and nominee directors across offshore jurisdictions (e.g., BVI, Panama, Cayman).",
            category="SHELL_COMPANY",
            red_flags=["3+ corporate nominee tiers", "Offshore registration", "Rapid pass-through of funds", "Lack of apparent commercial purpose"],
        )
        self.remember_typology(
            typology_name="Sanction Evasion Corridor Flight",
            description="Routing funds from or through high-risk/grey-list corridors with sudden jurisdiction changes.",
            category="SANCTIONS_EVASION",
            red_flags=["FATF grey list matches", "Dual-use goods narratives", "Intermediary bank hops", "Complex cross-border routing"],
        )
        self.remember_typology(
            typology_name="High-Velocity Account Cycling",
            description="Accounts receiving sudden massive inflows and immediately draining balances via foreign wires.",
            category="MONEY_MULE",
            red_flags=["Inflow and immediate outflow", "Zero overnight balance retention", "New account high activity"],
        )

    # -------------------------------------------------------------------------
    # Tier 4: User Preferences
    # -------------------------------------------------------------------------
    def get_user_preference(self, user_id: str = "default") -> dict[str, Any]:
        """Fetch user preferences (with fallback to default)."""
        if user_id in self._user_preferences:
            return dict(self._user_preferences[user_id])

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT settings_json FROM officer_preferences WHERE officer_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                prefs = json.loads(row[0])
                self._user_preferences[user_id] = prefs
                return prefs

        return dict(self._user_preferences["default"])

    def set_user_preference(self, user_id: str, settings: dict[str, Any]) -> None:
        """Update preferences for a compliance officer."""
        merged = dict(self.get_user_preference(user_id))
        merged.update(settings)
        self._user_preferences[user_id] = merged

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO officer_preferences (officer_id, settings_json) VALUES (?, ?)",
                (user_id, json.dumps(merged)),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Vector Embedding Utilities
    # -------------------------------------------------------------------------
    def _embed(self, text: str) -> list[float]:
        """Generate normalized bag-of-words vector embedding."""
        vector = [0.0] * self._dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            idx = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self._dimensions
            vector[idx] += 1.0
        magnitude = math.sqrt(sum(val * val for val in vector)) or 1.0
        return [val / magnitude for val in vector]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        return sum(a * b for a, b in zip(left, right))


# Global singleton instance for easy import across agent runtime
memory_store = HierarchicalMemoryStore()