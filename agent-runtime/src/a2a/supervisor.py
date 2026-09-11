from .protocol import A2AMessageEnvelope


class HandoffBlockedError(ValueError):
    pass


class MultiAgentSupervisor:
    def __init__(self, minimum_confidence: float = 0.85) -> None:
        self.minimum_confidence = minimum_confidence
        self.block_events: list[dict] = []

    def evaluate_handoff(self, envelope: A2AMessageEnvelope) -> bool:
        if envelope.confidence_score < self.minimum_confidence:
            event = {"event": "anti_amplification_block", "message_id": envelope.message_id, "confidence_score": envelope.confidence_score, "minimum_confidence": self.minimum_confidence}
            self.block_events.append(event)
            raise HandoffBlockedError(f"A2A handoff blocked: confidence {envelope.confidence_score:.3f} is below {self.minimum_confidence:.3f}")
        return True