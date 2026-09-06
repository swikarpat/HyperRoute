import os
import sys

# Ensure root and generated directories are in Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "generated"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from src.adk_workflow import ApexFraudInvestigationADK
from src.fsm_client import FsmEngineClient

app = FastAPI(title="ApexGateway ADK Agent Runtime", version="1.0.0")
fsm_client = FsmEngineClient()


class FraudAlertRequest(BaseModel):
    account_id: str
    amount_usd: float
    sender_country: str
    receiver_country: str
    narrative: str
    workflow_id: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "HEALTHY", "engine": "ADK + C++20 FSM via gRPC"}


@app.post("/api/v1/investigate")
def run_investigation(request: FraudAlertRequest):
    case_id = request.workflow_id or f"case-{uuid.uuid4().hex[:8]}"

    # 1. Hardware Guardrail SIMD inspection on text narrative
    is_clean, mask, sanitized = fsm_client.scan_tokens(case_id, request.narrative)
    if not is_clean:
        raise HTTPException(
            status_code=400,
            detail=f"Guardrail Block: Prohibited token pattern detected (Mask: {mask})"
        )

    # 2. Run ADK Agent Investigation
    try:
        adk_pipeline = ApexFraudInvestigationADK(workflow_id=case_id)
        result = adk_pipeline.execute_investigation(request.model_dump())
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal pipeline error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)