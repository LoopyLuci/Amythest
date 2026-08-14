"""Tests for new components: module index, usage tracker, checkpoint enhancements, smoke demo."""

from __future__ import annotations

from pathlib import Path

import pytest

from amythest.core.checkpoint import CheckpointManager
from amythest.core.module_index import ModuleIndex
from amythest.core.usage import UsageTracker, UsageRecord
from amythest.examples.smoke import run_smoke
from amythest.package import write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType
from amythest.core.manager import ModuleManager


def test_checkpoint_manager_round_trip(tmp_path: Path) -> None:
    cm = CheckpointManager(tmp_path / "ckpt")
    cm.create(["python-3.12-knowledge"], metadata={"note": "round-trip"})
    latest = cm.latest()
    assert latest is not None
    assert latest.active_modules == ["python-3.12-knowledge"]
    rolled = cm.rollback(latest)
    assert rolled.active_modules == ["python-3.12-knowledge"]


def test_usage_tracker_emits_summary(tmp_path: Path) -> None:
    tracker = UsageTracker(tmp_path / "usage.db")
    tracker.record(UsageRecord(task_category="qa", module_name="python-3.12-knowledge", module_version="1.0.0", active=True, helpful=True, timestamp=__import__("datetime").datetime.utcnow()))
    rate = tracker.helpful_rate("python-3.12-knowledge", "1.0.0")
    assert rate == 1.0


def test_module_index_fallback_without_embedder(tmp_path: Path) -> None:
    index_path = tmp_path / "modules.db"
    idx = ModuleIndex(index_path)
    idx.build([
        {"name": "python-3.12-knowledge", "description": "Python stdlib knowledge", "tags": ["python"], "version": "1.0.0"}
    ])
    results = idx.search(type("Task", (), {"description": "python list comprehension"})(), top_k=1)
    assert len(results) == 1
    assert results[0].name == "python-3.12-knowledge"


def test_smoke_demo_runs() -> None:
    result = run_smoke()
    assert isinstance(result, dict)
    assert result.get("modules_installed", 0) >= 1


def test_manager_rebuilds_index_after_install(tmp_path: Path) -> None:
    db = ModuleDatabase(tmp_path / ".amythest" / "modules")
    index_path = tmp_path / ".amythest" / "modules" / "module_index.db"
    manager = ModuleManager(db, index_path=index_path)
    manifest = ModuleManifest(
        name="indexed-module",
        version="1.0.0",
        author="test",
        description="Index test module",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "indexed.apkg", manifest)
    manager.install_package(pkg)
    assert index_path.exists()


def test_manager_rebuilds_index_after_activate(tmp_path: Path) -> None:
    db = ModuleDatabase(tmp_path / ".amythest" / "modules")
    index_path = tmp_path / ".amythest" / "modules" / "module_index.db"
    manager = ModuleManager(db, index_path=index_path)
    manifest = ModuleManifest(
        name="activate-index",
        version="1.0.0",
        author="test",
        description="Activate index test",
        module_type=ModuleType.SKILL,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "activate.apkg", manifest)
    manager.install_package(pkg)
    manager.activate("activate-index", "1.0.0")
    assert index_path.exists()
