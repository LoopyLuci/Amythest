"""Smoke-test the Amythest runtime without user interaction."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from amythest.core.checkpoint import CheckpointManager
from amythest.core.hitl import ActionType, HITLEngine
from amythest.core.module_index import ModuleIndex
from amythest.core.usage import UsageRecord, UsageTracker
from amythest.examples.real_builder import build_real_knowledge_module, build_real_skill_module, install_real_examples
from amythest.storage.database import ModuleDatabase


def run_smoke() -> dict:
    out = Path(__file__).resolve().parent.parent / "modules"
    db_root = Path.home() / ".amythest" / "modules"
    build_real_knowledge_module(out)
    build_real_skill_module(out)
    install_real_examples(db_root, out)

    db = ModuleDatabase(db_root)
    modules = db.list_modules()
    index = ModuleIndex(out / ".amythest" / "module_index.db")
    index.build([m.manifest for m in modules])
    recs = index.search(type("Task", (), {"description": "python asyncio taskgroups and exceptions"})(), top_k=3)

    tracker = UsageTracker(out / ".amythest" / "usage.db")
    tracker.record(UsageRecord(task_category="python", module_name="python-3.12-knowledge", module_version="1.1.0", active=True, helpful=True, timestamp=datetime.utcnow()))

    cp = CheckpointManager(out / "checkpoints").create(["python-3.12-knowledge"], metadata={"smoke": True})
    hitl = HITLEngine()
    req = hitl.evaluate(ActionType.TOOL_CALL, "run shell", payload={"cmd": "ls"})
    hitl.approve(req.id)

    return {
        "modules_installed": len(modules),
        "recommendations": [r.name for r in recs],
        "checkpoint": str(cp.path),
        "hitl_queue": len(hitl.queue),
        "hitl_history": len(hitl.history),
    }


if __name__ == "__main__":
    print(run_smoke())
