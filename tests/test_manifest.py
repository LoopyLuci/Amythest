"""Tests for module artifact manifest and package hash integrity."""

from __future__ import annotations

from pathlib import Path

import pytest

from amythest.package import read_apkg, sha256_file, write_apkg
from amythest.types import ModuleManifest, ModuleType


def test_write_apkg_stamps_sha256(tmp_path: Path) -> None:
    manifest = ModuleManifest(
        name="versioned-module",
        version="0.2.0",
        author="test",
        description="Versioned artifact",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="distilgpt2",
        base_model_version="2",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "versioned.apkg", manifest, files={})
    assert pkg.exists()
    data = read_apkg(pkg)
    assert data["manifest"] is not None
    assert data["manifest"].sha256 is not None
    assert len(data["manifest"].sha256) == 64


def test_read_apkg_roundtrip_metadata(tmp_path: Path) -> None:
    manifest = ModuleManifest(
        name="roundtrip",
        version="1.0.0",
        author="test",
        description="Roundtrip metadata",
        module_type=ModuleType.SKILL,
        base_model_name="amythest-base",
        base_model_version="1",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(tmp_path / "roundtrip.apkg", manifest, files={"index/chunks.jsonl": b"chunk1"})
    data = read_apkg(pkg)
    loaded = data["manifest"]
    assert loaded.name == manifest.name
    assert loaded.version == manifest.version
    assert loaded.base_model_name == manifest.base_model_name
    assert loaded.base_model_architecture == manifest.base_model_architecture
    assert "index/chunks.jsonl" in data["files"]
