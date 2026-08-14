from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel

from amythest.backend.interface import GenerationRequest
from amythest.backend.local import LocalBackend
from amythest.core.checkpoint import Checkpoint, CheckpointManager
from amythest.core.hitl import ActionType, HITLEngine
from amythest.core.manager import ModuleManager
from amythest.core.usage import UsageRecord, UsageTracker
from amythest.storage.database import ModuleDatabase

app = FastAPI(title="Amythest Runtime")

_db = ModuleDatabase(Path.home() / ".amythest" / "modules")
_index_path = Path.home() / ".amythest" / "modules" / "module_index.db"
_manager = ModuleManager(_db, index_path=_index_path)
_hitl = HITLEngine()
_usage = UsageTracker(Path.home() / ".amythest" / "usage.db")
_checkpoint_manager = CheckpointManager(Path.home() / ".amythest" / "checkpoints")


class EvaluateBody(BaseModel):
    action: str
    description: str
    payload: dict | None = None


class CheckpointBody(BaseModel):
    metadata: dict | None = None


class RollbackBody(BaseModel):
    checkpoint_path: str | None = None


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


class CompletionBody(BaseModel):
    prompt: str
    max_tokens: int = 64
    temperature: float = 0.2
    top_p: float = 0.95
    model: str | None = None


class CompletionOut(BaseModel):
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    active_modules: list[str] | None = None


class UsageRecordBody(BaseModel):
    task_category: str
    module_name: str
    module_version: str
    active: bool
    helpful: bool | None = None


_backend_instance: LocalBackend | None = None


def _local_backend() -> LocalBackend:
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = LocalBackend()
    return _backend_instance


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


@app.post("/recommend")
def recommend_modules(body: RecommendBody) -> list[dict]:
    results = _manager.recommend_modules(body.description, top_k=body.top_k)
    return [{"name": r.name, "version": r.version, "score": r.score, "reason": r.reason} for r in results]


@app.get("/metrics")
def metrics() -> list[dict]:
    modules = _manager.db.list_modules()
    active = _manager.active_modules()
    hitl_len = len(_hitl.queue)
    return [
        {"name": "modules_total", "value": float(len(modules)), "unit": "count"},
        {"name": "modules_active", "value": float(len(active)), "unit": "count"},
        {"name": "hitl_queue_depth", "value": float(hitl_len), "unit": "count"},
    ]


@app.post("/v1/completions", response_model=CompletionOut)
def v1_completions(body: CompletionBody) -> dict:
    backend = _local_backend()
    backend.ensure_model(body.model)
    request = GenerationRequest(
        prompt=body.prompt,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        top_p=body.top_p,
    )
    response = backend.generate(request)
    return {
        "text": response.text,
        "model": response.model,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "active_modules": response.active_modules,
    }


@app.post("/usage")
def record_usage(body: UsageRecordBody) -> dict:
    record = UsageRecord(
        task_category=body.task_category,
        module_name=body.module_name,
        module_version=body.module_version,
        active=body.active,
        helpful=body.helpful,
        timestamp=__import__("datetime").datetime.utcnow(),
    )
    _usage.record(record)
    return {"recorded": True}


@app.get("/usage/rate")
@app.post("/usage/rate")
def usage_rate(module_name: str = Query(...), module_version: str = Query(...)) -> dict:
    rate = _usage.helpful_rate(module_name, module_version)
    return {"module_name": module_name, "module_version": module_version, "helpful_rate": rate}


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


@app.post("/checkpoint")
def create_checkpoint(body: CheckpointBody) -> dict:
    checkpoint = _checkpoint_manager.create(
        active_modules=[m.manifest.name + "==" + m.manifest.version for m in _manager.active_modules()],
        metadata=body.metadata or {},
    )
    return {"checkpoint": str(checkpoint.path)}


@app.post("/rollback")
def rollback(body: RollbackBody) -> dict:
    target: Checkpoint | None = None
    if body.checkpoint_path:
        target = Checkpoint(path=Path(body.checkpoint_path))
    resolved = _checkpoint_manager.rollback(target)
    return {"rolled_back_to": str(resolved.path), "active_modules": resolved.active_modules}


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
