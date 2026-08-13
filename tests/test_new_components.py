"""Tests for new components: module index, usage tracker, checkpoint enhancements, smoke demo."""

from __future__ import annotations

from pathlib import Path

import pytest

from amythest.core.checkpoint import CheckpointManager
from amythest.core.hitl import ActionType, HITLEngine
from amythest.core.module_index import ModuleIndex
from amythest.core.usage import UsageTracker
from amythest.encoding.validator import validate_package


def test_module_index_build_and_search(tmp_path: Path):
    modules = [
        {"name": "python-knowledge", "description": "Python language knowledge", "tags": ["python"], "version": "1.0.0"},
        {"name": "docker-tools", "description": "Docker container tools", "tags": ["docker"], "version": "1.0.0"},
    ]
    idx = ModuleIndex(tmp_path / "index.db")
    idx.build(modules)
    recs = idx.search(type("Task", (), {"description": "python asyncio"})(), top_k=1)
    assert recs and recs[0].name == "python-knowledge"


def test_usage_tracker_roundtrip(tmp_path: Path):
    tracker = UsageTracker(tmp_path / "usage.db")
    from datetime import datetime
    from amythest.core.usage import UsageRecord
    tracker.record(UsageRecord(task_category="python", module_name="python-knowledge", module_version="1.0.0", active=True, helpful=True, timestamp=datetime.utcnow()))
    rate = tracker.helpful_rate("python-knowledge", "1.0.0")
    assert rate == 1.0


def test_checkpoint_with_model_state(tmp_path: Path):
    mgr = CheckpointManager(tmp_path / "checkpoints")
    from amythest.backend.local import ModelState
    cp = mgr.create(["python-knowledge"], metadata={"step": 1}, model_state=ModelState(model_name="base", weight_hash="abc123", device="cpu"), adapter_shards=["sha1"])
    assert cp.path.exists()
    raw = (cp.path / "manifest.json").read_text(encoding="utf-8")
    assert "adapter_shards" in raw
    assert "model" in raw


def test_validator_flags_missing_index():
    from amythest.package import write_apkg
    from amythest.types import ModuleManifest, ModuleType
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "m.apkg"
        write_apkg(path, ModuleManifest(name="x", version="0.1.0", author="a", description="d", module_type=ModuleType.KNOWLEDGE, base_model_name="b", base_model_version="0.1.0", base_model_architecture="dense"))
        result = validate_package(path)
        assert result.ok
        assert any("index/chunks.jsonl" in w for w in result.warnings)
