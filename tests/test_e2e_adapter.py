"""End-to-end test: package extraction -> install -> inject adapter path."""

from __future__ import annotations

from pathlib import Path

import pytest

from amythest.backend.local import LocalBackend
from amythest.core.manager import ModuleManager
from amythest.encoding.trainer import extract_adapter_dir
from amythest.package import write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType


def test_extract_adapter_dir_from_apkg(tmp_path: Path) -> None:
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir()
    manifest = ModuleManifest(
        name="fake-adapter",
        version="0.1.0",
        author="test",
        description="Fake adapter package",
        module_type=ModuleType.SKILL,
        base_model_name="distilgpt2",
        base_model_version="1",
        base_model_architecture="dense-70b",
    )
    files = {
        "weights/adapter.safetensors": b"fake-bytes",
        "weights/adapter_config.json": b'{"base_model_name":"distilgpt2"}',
    }
    pkg = write_apkg(out_dir / "fake.apkg", manifest, files=files)
    adapter_dir = extract_adapter_dir(pkg, dest=tmp_path / "extracted")
    assert (adapter_dir / "adapter.safetensors").exists()
    assert (adapter_dir / "adapter_config.json").exists()


def test_inject_modules_extracts_apkg(tmp_path: Path) -> None:
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir()
    manifest = ModuleManifest(
        name="inject-module",
        version="0.1.0",
        author="test",
        description="Inject test module",
        module_type=ModuleType.SKILL,
        base_model_name="distilgpt2",
        base_model_version="1",
        base_model_architecture="dense-70b",
    )
    files = {
        "weights/adapter.safetensors": b"fake-bytes",
        "weights/adapter_config.json": b'{"base_model_name":"distilgpt2","peft_type":"LORA","task_type":"CAUSAL_LM"}',
    }
    pkg = write_apkg(out_dir / "inject.apkg", manifest, files=files)
    db = ModuleDatabase(tmp_path / ".amythest" / "modules")
    manager = ModuleManager(db, index_path=tmp_path / ".amythest" / "modules" / "module_index.db")
    manager.install_package(pkg)
    manager.activate(manifest.name, manifest.version, context="test")
    backend = LocalBackend(cache_dir=tmp_path / "cache")
    backend.ensure_model("distilgpt2")
    with pytest.raises((RuntimeError, ValueError)):
        backend.inject_modules([{"name": manifest.name, "adapter_path": str(pkg)}])
