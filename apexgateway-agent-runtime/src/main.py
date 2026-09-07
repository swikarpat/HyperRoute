import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.telemetry import setup_telemetry, flush_telemetry, get_traceparent_metadata
from src.aws_secrets import fetch_compliance_secrets
from src.classifier import classifier
from src.agents import orchestrator

tracer = setup_telemetry("apexgateway-agent-runtime")

@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_compliance_secrets()
    yield
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
    return {"status": "HEALTHY", "tier1": "ONLINE", "tier2_multi_agent": "ONLINE"}

@app.post("/api/v1/agent/evaluate")
async def evaluate_alert(alert: TransactionAlert):
    with tracer.start_as_current_span("agent.orchestration.evaluate") as span:
        alert_dict = alert.model_dump()

        # =====================================================================
        # TIER 1: Sub-Millisecond Statistical ML Screening
        # =====================================================================
        with tracer.start_as_current_span("tier1.tabular_ml_score") as ml_span:
            risk_score, is_suspicious, _ = classifier.predict(alert_dict)
            ml_span.set_attribute("ml.risk_score", round(risk_score, 4))
            ml_span.set_attribute("ml.is_suspicious", is_suspicious)

        span.set_attribute("alert.account_id", alert.account_id)
        span.set_attribute("alert.amount_usd", alert.amount_usd)
        span.set_attribute("alert.risk_score", round(risk_score, 4))

        dossier_data = None

        # =====================================================================
        # ROUTING DECISION: Fast-Path vs. Multi-Agent Reasoning Graph
        # =====================================================================
        if not is_suspicious:
            status = "AUTO_CLEARED"
            final_fsm_state = 4
            total_steps = 3
            routing_tier = "TIER_1_STATISTICAL_FAST_PATH"
        else:
            with tracer.start_as_current_span("tier2.multi_agent_investigation") as agent_span:
                dossier = await orchestrator.investigate(alert_dict)
                status = dossier.recommended_fsm_action
                final_fsm_state = dossier.proposed_fsm_state
                total_steps = 6
                routing_tier = "TIER_2_MULTI_AGENT_INVESTIGATION"
                dossier_data = dossier.model_dump()

                agent_span.set_attribute("agent.risk_level", dossier.risk_level)
                agent_span.set_attribute("agent.confidence", dossier.confidence_score)

        with tracer.start_as_current_span("fsm.grpc_handoff") as grpc_span:
            grpc_metadata = get_traceparent_metadata()
            grpc_span.set_attribute("grpc.metadata_count", len(grpc_metadata))

        trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")

    response = {
        "status": status,
        "routing_tier": routing_tier,
        "statistical_risk_score": round(risk_score, 4),
        "final_fsm_state": final_fsm_state,
        "total_steps_executed": total_steps,
        "trace_id": trace_id,
        "metadata_propagated": dict(grpc_metadata)
    }
    if dossier_data:
        response["investigation_dossier"] = dossier_data

    return response

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")
