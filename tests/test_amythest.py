"""Minimal verification tests for the Amythest prototype."""

from __future__ import annotations

from pathlib import Path

import pytest

from amythest.core.manager import ModuleManager
from amythest.package import ApkgError, read_apkg, write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType


@pytest.fixture()
def tmp_db(tmp_path: Path) -> ModuleDatabase:
    return ModuleDatabase(tmp_path / ".amythest" / "modules")


@pytest.fixture()
def manager(tmp_db: ModuleDatabase) -> ModuleManager:
    return ModuleManager(tmp_db)


def test_manifest_roundtrip():
    manifest = ModuleManifest(
        name="test-module",
        version="0.1.0",
        author="test",
        description="Test module",
        module_type=ModuleType.SKILL,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    data = manifest.to_json()
    loaded = ModuleManifest.from_json(data)
    assert loaded.name == manifest.name
    assert loaded.module_type == manifest.module_type


def test_package_roundtrip(tmp_path: Path):
    manifest = ModuleManifest(
        name="pkg-test",
        version="0.1.0",
        author="test",
        description="Package test",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg_path = write_apkg(tmp_path / "pkg-test.apkg", manifest, {"index/chunks.jsonl": b"hello"})
    loaded = read_apkg(pkg_path)
    assert loaded["manifest"].name == "pkg-test"
    assert loaded["files"]["index/chunks.jsonl"] == b"hello"


def test_invalid_package(tmp_path: Path):
    bad = tmp_path / "bad.apkg"
    bad.write_text("not-a-zip")
    with pytest.raises(ApkgError):
        read_apkg(bad)


def test_install_and_list(manager: ModuleManager, tmp_path: Path):
    manifest = ModuleManifest(
        name="demo-module",
        version="1.0.0",
        author="test",
        description="Demo module",
        module_type=ModuleType.TOOL,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "demo.apkg", manifest)
    manager.install_package(pkg)
    modules = manager.db.list_modules()
    assert len(modules) == 1
    assert modules[0].manifest.name == "demo-module"


def test_activate_deactivate(manager: ModuleManager, tmp_path: Path):
    manifest = ModuleManifest(
        name="toggle",
        version="0.1.0",
        author="test",
        description="Toggle module",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "toggle.apkg", manifest)
    manager.install_package(pkg)
    manager.activate("toggle", "0.1.0")
    assert manager.db.get("toggle", "0.1.0").active is True
    manager.deactivate("toggle", "0.1.0")
    assert manager.db.get("toggle", "0.1.0").active is False


def test_uninstall_active_blocked(manager: ModuleManager, tmp_path: Path):
    manifest = ModuleManifest(
        name="blocked",
        version="0.1.0",
        author="test",
        description="Blocked module",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "blocked.apkg", manifest)
    manager.install_package(pkg)
    manager.activate("blocked", "0.1.0")
    with pytest.raises(RuntimeError):
        manager.uninstall("blocked", "0.1.0")
