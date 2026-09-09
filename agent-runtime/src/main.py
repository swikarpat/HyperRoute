import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from google_adk.common.types import AgentTask

from src.telemetry import setup_telemetry, flush_telemetry, get_traceparent_metadata
from src.aws_secrets import fetch_compliance_secrets
from src.classifier import classifier
from src.graph import investigation_graph
from src.fsm_client import fsm_client

tracer = setup_telemetry("apexgateway-agent-runtime")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await investigation_graph.setup()
    fetch_compliance_secrets()
    yield
    await investigation_graph.shutdown()
    flush_telemetry()

app = FastAPI(title="ApexGateway Agent Runtime", version="1.0.0", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

class TransactionAlert(BaseModel):
    account_id: str
    amount_usd: float
    sender_country: str
    receiver_country: str
    narrative: str

@app.get("/health")
def health():
    return {"status": "HEALTHY", "tier2_workflow": "ONLINE", "fsm_bridge": "ONLINE"}

@app.post("/api/v1/agent/evaluate")
async def evaluate_alert(alert: TransactionAlert):
    with tracer.start_as_current_span("agent.orchestration.evaluate") as span:
        alert_dict = alert.model_dump()
        investigation_dossier = None

        # Tier 1: Sub-Millisecond Tabular Screening
        with tracer.start_as_current_span("tier1.tabular_ml_score") as ml_span:
            risk_score, is_suspicious, features = classifier.predict(alert_dict)
            ml_span.set_attribute("ml.risk_score", round(risk_score, 4))
            ml_span.set_attribute("ml.is_suspicious", is_suspicious)

        span.set_attribute("alert.account_id", alert.account_id)
        span.set_attribute("alert.amount_usd", alert.amount_usd)

        # Fast-Path vs. Tier 2 Multi-Agent Investigation
        if not is_suspicious:
            proposed_action = "CLEAR_TRANSACTION"
            routing_tier = "TIER_1_STATISTICAL_FAST_PATH"
            total_steps = 3
        else:
            with tracer.start_as_current_span("tier2.multi_agent_investigation"):
                task_data = {
                    "alert": alert_dict,
                    "features": features,
                    "ml_risk_score": round(risk_score, 4),
                    "ml_risk_level": "CRITICAL" if risk_score > 0.8 else "HIGH"
                }
                graph_result = await investigation_graph.run(AgentTask(data=task_data))
                final_message = await graph_result.output.get()
                investigation_dossier = final_message.data
                
                proposed_action = investigation_dossier.get("recommended_fsm_action", "ESCALATED_TO_HUMAN")
                routing_tier = "TIER_2_MULTI_AGENT_INVESTIGATION"
                total_steps = 6

        # Tier 3: Deterministic C++20 FSM & RocksDB Commit
        trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
        grpc_metadata = get_traceparent_metadata()

        final_fsm_state, audit_hash, fsm_latency_us = fsm_client.transition_state(
            trace_id=trace_id,
            alert_data=alert_dict,
            action_name=proposed_action,
            agent_dossier=investigation_dossier,
            metadata=grpc_metadata
        )

    response = {
        "status": proposed_action,
        "routing_tier": routing_tier,
        "statistical_risk_score": round(risk_score, 4),
        "final_fsm_state": final_fsm_state,
        "audit_dossier_hash": audit_hash,
        "fsm_transition_latency": f"{fsm_latency_us} μs" if fsm_latency_us > 0 else "FALLBACK_MOCK",
        "total_steps_executed": total_steps,
        "trace_id": trace_id,
        "metadata_propagated": dict(grpc_metadata)
    }

    if investigation_dossier:
        response["investigation_dossier"] = investigation_dossier

    return response

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")
