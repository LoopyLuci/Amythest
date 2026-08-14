"""Expanded verification tests for Amythest backend, encoding, HITL, analyzer, and checkpoint."""

from __future__ import annotations

from pathlib import Path

from amythest.backend.compositor import compose_prompt
from amythest.core.analyzer import Task, TaskAnalyzer
from amythest.core.checkpoint import CheckpointManager
from amythest.core.hitl import ActionType, Decision, HITLEngine, Policy
from amythest.encoding.trainer import build_training_records, save_jsonl


def test_compose_prompt_injects_module_parts():
    modules = [
        {"type": "knowledge", "chunks": ["alpha", "beta"]},
        {"type": "skill", "system_prompt": "be helpful"},
    ]
    composed = compose_prompt("hello", modules)
    assert "[MODULE KNOWLEDGE]" in composed
    assert "[MODULE BEHAVIOR]" in composed
    assert "[USER QUERY]\nhello" in composed


def test_analyzer_recommends_modules():
    analyzer = TaskAnalyzer()
    modules = [
        {"name": "python-knowledge", "description": "Python language knowledge", "tags": ["python"], "version": "1.0.0"},
        {"name": "docker-tools", "description": "Docker container tools", "tags": ["docker"], "version": "1.0.0"},
    ]
    recs = analyzer.recommend(Task(description="python asyncio usage"), modules)
    assert recs[0].name == "python-knowledge"


def test_hitl_queue_and_decisions():
    engine = HITLEngine(policies=[Policy(action=ActionType.TOOL_CALL, auto_approve=False)])
    req = engine.evaluate(ActionType.TOOL_CALL, "run shell command")
    assert req.decided is False
    assert len(engine.queue) == 1
    approved = engine.approve(req.id)
    assert approved.decision == Decision.APPROVED
    assert len(engine.queue) == 0


def test_checkpoint_manager_roundtrip(tmp_path: Path):
    mgr = CheckpointManager(tmp_path / "checkpoints")
    cp = mgr.create(["python-3.12-knowledge"], metadata={"task": "demo"})
    assert cp.path.exists()
    latest = mgr.latest()
    assert latest is not None
    assert latest.active_modules == ["python-3.12-knowledge"]


def test_trainer_records_and_jsonl(tmp_path: Path):
    records = build_training_records(["alpha", "", "beta"])
    assert len(records) == 2
    out = tmp_path / "out.jsonl"
    save_jsonl(records, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
