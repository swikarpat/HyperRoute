from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class CryptographicTracer:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def trace(self, execution_id: str, agent_name: str, action: str, payload: Any, timestamp: str | None = None) -> dict[str, Any]:
        event = {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id,
            "agent_name": agent_name,
            "action": action,
            "payload_hash": hashlib.sha256(self._canonical(payload)).hexdigest(),
            "parent_hash": self.records[-1]["hash"] if self.records else "0" * 64,
            "event_id": str(uuid4()),
        }
        event["hash"] = self._record_hash(event)
        self.records.append(event)
        return dict(event)

    def verify_chain_integrity(self) -> bool:
        parent = "0" * 64
        for record in self.records:
            if record.get("parent_hash") != parent or record.get("hash") != self._record_hash(record):
                return False
            parent = record["hash"]
        return True

    @staticmethod
    def _canonical(value: Any) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    @classmethod
    def _record_hash(cls, record: dict[str, Any]) -> str:
        fields = {key: value for key, value in record.items() if key != "hash"}
        return hashlib.sha256(cls._canonical(fields)).hexdigest()