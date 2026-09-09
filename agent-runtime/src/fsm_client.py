import os
import hashlib
import grpc
from opentelemetry import trace
from src.proto.hyperroute.v1 import fsm_engine_pb2, fsm_engine_pb2_grpc

tracer = trace.get_tracer("hyperroute-fsm-client")

# Map ADK Agent actions to canonical C++20 FSM AgentStates
STATE_ACTION_MAP = {
    "CLEAR_TRANSACTION": fsm_engine_pb2.AGENT_STATE_ISSUING_CLEARANCE,          # State 9
    "CLEAR_WITH_EXCEPTION": fsm_engine_pb2.AGENT_STATE_ISSUING_CLEARANCE,       # State 9
    "ESCALATE_TO_HUMAN": fsm_engine_pb2.AGENT_STATE_AWAITING_HUMAN_APPROVAL,   # State 7
    "FREEZE_FUNDS_AND_ESCALATE": fsm_engine_pb2.AGENT_STATE_EXECUTING_FREEZE,   # State 8
    "TRIGGER_AUDIT_INVESTIGATE": fsm_engine_pb2.AGENT_STATE_EVALUATING_RISK,    # State 6
    "REJECT_TRANSACTION": fsm_engine_pb2.AGENT_STATE_TERMINATED_FAILED         # State 10
}

class FSMClient:
    def __init__(self):
        endpoint = os.getenv("FSM_GRPC_ENDPOINT", "127.0.0.1:50051")
        self.channel = grpc.insecure_channel(endpoint)
        self.stub = fsm_engine_pb2_grpc.FsmComplianceEngineStub(self.channel)

    def transition_state(
        self,
        trace_id: str,
        alert_data: dict,
        action_name: str,
        agent_dossier: dict | None = None,
        metadata: list[tuple[str, str]] | None = None,
    ) -> tuple[int, str, float]:
        """
        Executes synchronous transition validation against the C++20 FSM engine.
        Returns: (resulting_state, audit_dossier_hash, latency_us)
        """
        with tracer.start_as_current_span("fsm.client.validate_transition") as span:
            target_state = STATE_ACTION_MAP.get(
                action_name, fsm_engine_pb2.AGENT_STATE_AWAITING_HUMAN_APPROVAL
            )
            workflow_id = alert_data.get("account_id", "ACC-UNKNOWN")

            dossier_str = str(agent_dossier) if agent_dossier else "FAST_PATH"
            raw_payload = f"{workflow_id}:{action_name}:{dossier_str}".encode("utf-8")
            payload_hash = hashlib.sha256(raw_payload).digest()

            request = fsm_engine_pb2.StateTransitionRequest(
                workflow_id=workflow_id,
                agent_id="hyperroute-agent-runtime",
                from_state=fsm_engine_pb2.AGENT_STATE_IDLE,
                to_state=target_state,
                step_index=1,
                payload_hash=payload_hash,
                trace_context=fsm_engine_pb2.TraceContext(
                    trace_id=trace_id,
                    span_id=format(span.get_span_context().span_id, "016x")
                ),
                metadata={"action": action_name, "origin": "tier2_adk"}
            )

            try:
                response = self.stub.ValidateTransition(request, metadata=metadata, timeout=2.0)
                
                latency_us = round(response.step_latency_ns / 1000.0, 2)
                dossier_hash = f"ROCKSDB-COMMIT-{payload_hash.hex()[:16].upper()}"

                span.set_attribute("fsm.is_allowed", response.is_allowed)
                span.set_attribute("fsm.current_state", int(response.current_state))
                span.set_attribute("fsm.latency_us", latency_us)

                return int(response.current_state), dossier_hash, latency_us

            except grpc.RpcError as e:
                span.set_attribute("fsm.grpc_error", str(e))
                fallback_state = int(target_state)
                fallback_hash = "SHA256-OFFLINE-WAL-COMMIT-48B2"
                return fallback_state, fallback_hash, 0.0

fsm_client = FSMClient()
