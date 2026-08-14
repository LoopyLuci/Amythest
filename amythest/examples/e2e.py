"""End-to-end script: create, install, activate, compose, checkpoint, validate, and serve."""

from __future__ import annotations

from pathlib import Path

from amythest.core.analyzer import Task, TaskAnalyzer
from amythest.core.checkpoint import CheckpointManager
from amythest.core.manager import ModuleManager
from amythest.encoding.validator import validate_package
from amythest.examples.real_builder import (
    build_real_knowledge_module,
    build_real_skill_module,
)
from amythest.storage.database import ModuleDatabase


def run_e2e(output_dir: Path, db_root: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    kp = build_real_knowledge_module(output_dir)
    sp = build_real_skill_module(output_dir)
    db = ModuleDatabase(db_root)
    mgr = ModuleManager(db)
    mgr.install_package(kp)
    mgr.install_package(sp)
    mgr.activate("python-3.12-knowledge", "1.1.0", context="e2e")
    mgr.activate("agentic-runtime-skills", "1.1.0", context="e2e")
    kp_val = validate_package(kp)
    sp_val = validate_package(sp)
    cp_mgr = CheckpointManager(output_dir / "checkpoints")
    cp = cp_mgr.create([m.manifest.name for m in mgr.active_modules()])
    analyzer = TaskAnalyzer()
    recs = analyzer.recommend(
        Task(description="python asyncio task groups and exception handling"),
        [m.manifest for m in mgr.active_modules()],
    )
    return {
        "knowledge_path": str(kp),
        "skill_path": str(sp),
        "active_modules": [m.manifest.name for m in mgr.active_modules()],
        "knowledge_valid": kp_val.ok,
        "skill_valid": sp_val.ok,
        "recommendations": [r.name for r in recs],
        "checkpoint": str(cp.path),
    }


if __name__ == "__main__":
    result = run_e2e(
        Path(__file__).resolve().parent.parent / "modules",
        Path.home() / ".amythest" / "modules",
    )
    for k, v in result.items():
        print(f"{k}: {v}")
