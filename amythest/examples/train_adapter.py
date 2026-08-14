"""Train and package a tiny LoRA adapter for a small model."""
from __future__ import annotations

import json
from pathlib import Path

from amythest.encoding.trainer import build_training_records, save_jsonl
from amythest.encoding.pipeline import encode_training_records
from amythest.types import ModuleManifest, ModuleType
from amythest.package import write_apkg
from amythest.core.manager import ModuleManager
from amythest.storage.database import ModuleDatabase


def main() -> None:
    out_dir = Path("tmp_training_artifacts")
    out_dir.mkdir(exist_ok=True)
    records = build_training_records([
        "The capital of France is Paris.",
        "Python is a programming language.",
        "Amythest modules can be activated and deactivated.",
    ])
    save_jsonl(records, out_dir / "train.jsonl")
    encoded = encode_training_records(records)
    save_jsonl(encoded, out_dir / "encoded.jsonl")
    manifest = ModuleManifest(
        name="demo-trained-module",
        version="0.1.0",
        author="amythest",
        description="Demo trained module from local corpus",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="distilgpt2",
        base_model_version="1",
        base_model_architecture="dense-70b",
    )
    pkg = write_apkg(out_dir / "demo.apkg", manifest, extra={"index/chunks.jsonl": "\n".join(encoded).encode("utf-8")})
    db = ModuleDatabase(Path.home() / ".amythest" / "modules")
    manager = ModuleManager(db, index_path=Path.home() / ".amythest" / "modules" / "module_index.db")
    stored = manager.install_package(pkg)
    manager.activate(manifest.name, manifest.version, context="train")
    print(json.dumps({"installed": str(stored.path), "active_modules": len(manager.active_modules())}, indent=2))


if __name__ == "__main__":
    main()
