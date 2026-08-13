from fastapi import FastAPI
from pydantic import BaseModel

from amythest.core.manager import ModuleManager
from amythest.core.hitl import ActionType, HITLEngine
from amythest.storage.database import ModuleDatabase
from pathlib import Path

app = FastAPI(title="Amythest Runtime")

_db = ModuleDatabase(Path.home() / ".amythest" / "modules")
_index_path = Path.home() / ".amythest" / "modules" / "module_index.db"
_manager = ModuleManager(_db, index_path=_index_path)
_hitl = HITLEngine()


class EvaluateBody(BaseModel):
    action: str
    description: str
    payload: dict | None = None


class ModuleOut(BaseModel):
    name: str
    version: str
    type: str
    active: bool


class StatusOut(BaseModel):
    active_count: int
    active_modules: list[dict]


class RecommendBody(BaseModel):
    description: str
    top_k: int = 5


class RecommendationOut(BaseModel):
    name: str
    version: str
    score: float
    reason: str


@app.get("/status")
def status() -> StatusOut:
    return StatusOut(**_manager.compose())


@app.get("/modules")
def list_modules() -> list[ModuleOut]:
    return [
        ModuleOut(
            name=m.manifest.name,
            version=m.manifest.version,
            type=m.manifest.module_type.value,
            active=m.active,
        )
        for m in _manager.db.list_modules()
    ]


@app.post("/modules/{name}/{version}/activate")
def activate_module(name: str, version: str) -> dict:
    _manager.activate(name, version, context="api")
    return {"activated": name, "version": version}


@app.post("/modules/{name}/{version}/deactivate")
def deactivate_module(name: str, version: str) -> dict:
    _manager.deactivate(name, version)
    return {"deactivated": name, "version": version}


@app.post("/recommend", response_model=list[RecommendationOut])
def recommend_modules(body: RecommendBody) -> list[dict]:
    results = _manager.recommend_modules(body.description, top_k=body.top_k)
    return [{"name": r.name, "version": r.version, "score": r.score, "reason": r.reason} for r in results]


@app.post("/hitl/evaluate")
def evaluate_hitl(body: EvaluateBody) -> dict:
    action = ActionType(body.action)
    req = _hitl.evaluate(action, body.description, payload=body.payload)
    return {
        "id": req.id,
        "action": req.action.value,
        "decided": req.decided,
        "decision": req.decision.value if req.decision else None,
    }


@app.get("/hitl/queue")
def hitl_queue() -> list[dict]:
    return [
        {
            "id": r.id,
            "action": r.action.value,
            "description": r.description,
            "decided": r.decided,
            "decision": r.decision.value if r.decision else None,
        }
        for r in _hitl.queue
    ]


@app.post("/hitl/{request_id}/approve")
def approve_hitl(request_id: str) -> dict:
    req = _hitl.approve(request_id)
    if not req:
        return {"error": "not_found"}
    return {"id": req.id, "decision": req.decision.value}


@app.post("/hitl/{request_id}/reject")
def reject_hitl(request_id: str) -> dict:
    req = _hitl.reject(request_id)
    if not req:
        return {"error": "not_found"}
    return {"id": req.id, "decision": req.decision.value}
