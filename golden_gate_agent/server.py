"""
FastAPI REST API Server for GoldenGate-Assembler: Type IIS Restriction Overhang Fidelity Agent.
"""
from typing import Dict, Any
from .models import FrontierPayload
from .agents import GoldenGateCoordinator

coordinator = GoldenGateCoordinator()


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="GoldenGate-Assembler: Type IIS Restriction Overhang Fidelity Agent",
            description="Optimizes 4-base 5'-overhang sets (BsaI/BsmBI), calculating ligation fidelity matrices to guarantee >99% assembly accuracy.",
            version="2.0.0-FRONTIER",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = Field(default=28.5, allow_inf_nan=False, ge=-1e9, le=1e9)
            secondary_metric: float = Field(default=14.2, allow_inf_nan=False, ge=-1e9, le=1e9)
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = {}

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "golden-gate-assembly-overhang", "domain": "Synthetic Biology", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            return coordinator.process(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
