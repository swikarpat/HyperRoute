from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from pydantic import BaseModel, Field


class A2AMessageEnvelope(BaseModel):
    protocol_version: str = "A2A/1.0"
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_agent_id: str
    recipient_agent_id: str
    intent_capability: str
    payload_data: dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    task_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class A2ARouter:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[A2AMessageEnvelope], Any]] = {}

    def register(self, agent_id: str, handler: Callable[[A2AMessageEnvelope], Any]) -> None:
        self._handlers[agent_id] = handler

    def dispatch(self, envelope: A2AMessageEnvelope) -> Any:
        try:
            handler = self._handlers[envelope.recipient_agent_id]
        except KeyError as exc:
            raise LookupError(f"No A2A handler registered for {envelope.recipient_agent_id}") from exc
        return handler(envelope)