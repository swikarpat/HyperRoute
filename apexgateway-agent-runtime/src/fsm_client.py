import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
GEN_DIR = os.path.join(BASE_DIR, "generated")
if GEN_DIR not in sys.path:
    sys.path.insert(0, GEN_DIR)

import grpc
from typing import Tuple

from generated.apexgateway.v1 import fsm_engine_pb2 as pb
from generated.apexgateway.v1 import fsm_engine_pb2_grpc as pb_grpc


class FsmEngineClient:
    """gRPC Client communicating directly with the C++20 FSM Compliance Engine."""

    def __init__(self, target: str = "localhost:50051"):
        self.channel = grpc.insecure_channel(
            target,
            options=[
                ("grpc.max_receive_message_length", 16 * 1024 * 1024),
                ("grpc.max_send_message_length", 16 * 1024 * 1024),
            ],
        )
        self.stub = pb_grpc.FsmComplianceEngineStub(self.channel)

    def validate_transition(
        self,
        workflow_id: str,
        agent_id: str,
        from_state: int,
        to_state: int,
        step_index: int,
        trace_id: str = "trace-default",
    ) -> Tuple[bool, int, str, int]:
        request = pb.StateTransitionRequest(
            workflow_id=workflow_id,
            agent_id=agent_id,
            from_state=from_state,
            to_state=to_state,
            step_index=step_index,
            trace_context=pb.TraceContext(
                trace_id=trace_id,
                span_id=f"span-{step_index}",
                trace_flags=1
            ),
        )

        response: pb.StateTransitionResponse = self.stub.ValidateTransition(request)
        return (
            response.is_allowed,
            response.rejection_code,
            response.rejection_reason,
            response.step_latency_ns,
        )

    def scan_tokens(self, workflow_id: str, text: str) -> Tuple[bool, int, str]:
        def chunk_generator():
            yield pb.TokenInspectionChunk(
                workflow_id=workflow_id,
                sequence_number=1,
                token_text=text,
                is_final_chunk=True,
            )

        responses = self.stub.InspectTokenStream(chunk_generator())
        for resp in responses:
            return resp.is_clean, resp.violation_mask, resp.sanitized_text
        return True, 0, text