import uvicorn
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.google_adk.common.types import AgentTask

from src.telemetry import setup_telemetry, flush_telemetry, get_traceparent_metadata
from src.aws_secrets import fetch_compliance_secrets
from src.classifier import classifier
from src.graph import investigation_graph
from src.fsm_client import fsm_client
from src.memory.memory_store import memory_store
from src.google_adk.planner import DynamicPlanner
from src.google_adk.reasoning import cognitive_engine

tracer = setup_telemetry("hyperroute-agent-runtime")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await investigation_graph.setup()
    fetch_compliance_secrets()
    yield
    await investigation_graph.shutdown()
    flush_telemetry()


app = FastAPI(title="HyperRoute Agent Runtime", version="2.0.0", lifespan=lifespan)

# Enable CORS for React 19 Frontend (:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)


class TransactionAlert(BaseModel):
    account_id: str
    amount_usd: float
    sender_country: str
    receiver_country: str
    narrative: str


class ChatQuery(BaseModel):
    query: str
    account_id: Optional[str] = None
    supervisor_notes: Optional[str] = None


@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "engine": "Google-ADK-Python3.14",
        "tier2_workflow": "ONLINE",
        "fsm_bridge": "ONLINE",
        "memory_subsystem": "4_TIER_ACTIVE",
        "cognitive_mode": "LIVE_GEMINI" if cognitive_engine.is_live else "OFFLINE_DETERMINISTIC_ZERO_SPEND",
    }


@app.post("/api/v1/agent/evaluate")
async def evaluate_alert(alert: TransactionAlert):
    with tracer.start_as_current_span("agent.orchestration.evaluate") as span:
        alert_dict = alert.model_dump()
        investigation_dossier = None

        # Reset short-term scratchpad & working state for fresh case
        memory_store.clear_scratchpad()
        memory_store.reset_working_state()
        memory_store.update_working_state(alert=alert_dict)

        # Google ADK Dynamic Planner: Formulate initial plan
        planner = DynamicPlanner(workflow_id=alert.account_id)
        plan_steps = planner.create_initial_plan(alert_dict)

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
                    "ml_risk_level": "CRITICAL" if risk_score > 0.8 else "HIGH",
                }
                graph_result = await investigation_graph.run(AgentTask(data=task_data))
                final_message = await graph_result.output.get()
                investigation_dossier = final_message.data

                # Observe entity findings & trigger dynamic replanning if required
                if "entity_findings" in investigation_dossier:
                    entity_step = next((s for s in plan_steps if s.target_capability == "ENTITY_RESOLUTION"), None)
                    if entity_step:
                        planner.observe_and_replan(entity_step, investigation_dossier["entity_findings"], alert_dict)

                if "sanctions_findings" in investigation_dossier:
                    sanctions_step = next((s for s in plan_steps if s.target_capability == "SANCTIONS_SCREENING"), None)
                    if sanctions_step:
                        planner.observe_and_replan(sanctions_step, investigation_dossier["sanctions_findings"], alert_dict)

                proposed_action = investigation_dossier.get("recommended_fsm_action", "ESCALATED_TO_HUMAN")
                routing_tier = "TIER_2_MULTI_AGENT_INVESTIGATION"
                total_steps = len(planner.plan) + 2

        # Tier 3: Deterministic C++20 FSM & RocksDB Commit
        trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
        grpc_metadata = get_traceparent_metadata()

        final_fsm_state, audit_hash, fsm_latency_us = fsm_client.transition_state(
            trace_id=trace_id,
            alert_data=alert_dict,
            action_name=proposed_action,
            agent_dossier=investigation_dossier,
            metadata=grpc_metadata,
        )

        # Tier 2: Persist to Long-term Memory
        memory_store.save_case(
            case_id=alert.account_id,
            account_id=alert.account_id,
            amount_usd=alert.amount_usd,
            sender_country=alert.sender_country,
            receiver_country=alert.receiver_country,
            status=proposed_action,
            fsm_state=final_fsm_state,
            risk_score=round(risk_score, 4),
            narrative=alert.narrative,
            dossier=investigation_dossier,
        )

    response = {
        "workflow_id": alert.account_id,
        "status": proposed_action,
        "routing_tier": routing_tier,
        "statistical_risk_score": round(risk_score, 4),
        "final_fsm_state": final_fsm_state,
        "audit_dossier_hash": audit_hash,
        "fsm_transition_latency": f"{fsm_latency_us} μs" if fsm_latency_us > 0 else "FALLBACK_MOCK",
        "total_steps_executed": total_steps,
        "transaction_amount": alert.amount_usd,
        "trace_id": trace_id,
        "metadata_propagated": dict(grpc_metadata),
        "dynamic_plan": planner.get_plan_summary(),
        "memory_status": {
            "scratchpad_items": len(memory_store.get_scratchpad()),
            "persisted_long_term": True,
        },
    }

    if investigation_dossier:
        response["investigation_dossier"] = investigation_dossier

    return response


@app.post("/api/v1/agent/chat")
async def chat_interrogate(chat: ChatQuery):
    """Interactive compliance copilot interrogation endpoint for human investigators."""
    account_id = chat.account_id or "ACC-CORP-4402"
    historical_case = memory_store.get_case(account_id)

    dossier = historical_case.get("dossier", {}) if historical_case else None
    active_alert = {
        "account_id": account_id,
        "amount_usd": historical_case.get("amount_usd", 0.0) if historical_case else 3400000.0,
        "sender_country": historical_case.get("sender_country", "SG") if historical_case else "SG",
        "receiver_country": historical_case.get("receiver_country", "US") if historical_case else "US",
        "narrative": historical_case.get("narrative", "") if historical_case else "",
    }

    # Format memory summary
    prior_cases = memory_store.query_entity_history(account_id, limit=3)
    matched_typologies = memory_store.recall_typologies(chat.query, threshold=0.50, limit=2)
    memory_summary = (
        f"- Active Scratchpad: {len(memory_store.get_scratchpad())} live step observations\n"
        f"- Long-term History: {len(prior_cases)} prior investigation(s) in SQLite store\n"
        f"- Semantic Typologies: {', '.join([t['name'] for t in matched_typologies]) if matched_typologies else 'None directly matched'}\n"
        f"- Officer Preferences: {memory_store.get_user_preference().get('risk_tolerance')} tolerance"
    )

    # If supervisor notes provided, update case in long-term memory
    if chat.supervisor_notes and historical_case:
        memory_store.save_case(
            case_id=account_id,
            account_id=account_id,
            amount_usd=active_alert["amount_usd"],
            sender_country=active_alert["sender_country"],
            receiver_country=active_alert["receiver_country"],
            status="HUMAN_OVERRIDE_APPROVED",
            fsm_state=9,  # Settled / Cleared
            risk_score=historical_case.get("risk_score", 0.0),
            narrative=active_alert["narrative"],
            dossier=dossier,
            supervisor_notes=chat.supervisor_notes,
        )

    reply_text = cognitive_engine.chat_interrogate(
        query=chat.query,
        active_alert=active_alert,
        dossier=dossier,
        memory_summary=memory_summary,
    )

    return {
        "reply": reply_text,
        "account_id": account_id,
        "fsm_state": historical_case.get("fsm_state", 7) if historical_case else 7,
        "memory_tier_used": ["Short-term Scratchpad", "Long-term Case Ledger", "Semantic Vector Store"],
    }


@app.get("/api/v1/agent/memory/{account_id}")
def inspect_memory(account_id: str):
    """Inspect all 4 tiers of memory for a given entity."""
    return {
        "account_id": account_id,
        "tier_1_short_term_scratchpad": memory_store.get_scratchpad(),
        "tier_2_long_term_history": memory_store.query_entity_history(account_id, limit=5),
        "tier_3_semantic_typologies": memory_store.recall_typologies("corporate nominee offshore structuring", threshold=0.45),
        "tier_4_user_preferences": memory_store.get_user_preference(),
    }


@app.get("/api/v1/agent/cases")
def list_cases(limit: int = 10):
    """List recent cases persisted in long-term memory."""
    return {"cases": memory_store.list_recent_cases(limit=limit)}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")
