"""Adapter artifact packaging and extraction verification."""

from __future__ import annotations

from pathlib import Path

import zipfile

import pytest

from amythest.encoding.trainer import extract_adapter_dir, package_module_outputs, write_adapter_bytes
from amythest.package import write_apkg
from amythest.types import ModuleManifest, ModuleType


def test_adapter_artifact_packaging(tmp_path: Path) -> None:
    manifest = ModuleManifest(
        name="inference-module",
        version="0.1.0",
        author="test",
        description="Inference verification module",
        module_type=ModuleType.SKILL,
        base_model_name="distilgpt2",
        base_model_version="1",
        base_model_architecture="dense-70b",
    )
    files = package_module_outputs(
        manifest_path=tmp_path / "manifest.json",
        adapter_bytes=b"fake-adapter-bytes",
        adapter_config={"base_model_name": "distilgpt2", "peft_type": "LORA", "task_type": "CAUSAL_LM"},
    )
    pkg = write_apkg(tmp_path / "inference.apkg", manifest, files=files)
    assert zipfile.is_zipfile(pkg)
    with zipfile.ZipFile(pkg, "r") as zf:
        names = zf.namelist()
    assert "weights/adapter.safetensors" in names
    assert "weights/adapter_config.json" in names
    extracted = extract_adapter_dir(pkg, dest=tmp_path / "extracted")
    assert (extracted / "adapter.safetensors").exists()
    assert (extracted / "adapter_config.json").exists()
    config = (extracted / "adapter_config.json").read_text(encoding="utf-8")
    assert "LORA" in config
    assert "distilgpt2" in config
