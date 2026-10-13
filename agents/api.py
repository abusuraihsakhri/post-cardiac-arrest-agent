"""
FastAPI REST API Server for Post Cardiac Arrest Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Post Cardiac Arrest Agent API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "post-cardiac-arrest-agent", "domain": "Clinical & Biomedical AI", "standard": "Synthetic demonstration; no clinical guideline implemented", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING_DEMO"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potential identifier detected; use synthetic data only.") from None
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potential identifier detected; use synthetic data only.") from None


@app.get("/api/audit/logs")
def api_audit_logs():
    # Full audit entries require access control, which this demo API does not provide.
    return {"entry_count": len(AuditLogger.get_trail()), "verified": AuditLogger.verify_integrity()}
