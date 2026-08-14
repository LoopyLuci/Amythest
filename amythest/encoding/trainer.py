"""Encode datasets into module artifacts: LoRA adapters and RAG indices."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path


def build_training_records(texts: Sequence[str]) -> list[dict]:
    return [{"text": t} for t in texts if t.strip()]


def save_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def package_module_outputs(
    *,
    manifest_path: Path,
    adapter_bytes: bytes | None = None,
    adapter_config: dict | None = None,
    chunks: list[str] | None = None,
    system_prompt: str | None = None,
    few_shot: list[dict] | None = None,
    tools: dict | None = None,
    tests: dict | None = None,
) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    if adapter_bytes:
        files["weights/adapter.safetensors"] = adapter_bytes
    if adapter_config:
        files["weights/adapter_config.json"] = json.dumps(adapter_config).encode("utf-8")
    if chunks:
        payload = "\n".join(chunks).encode("utf-8")
        files["index/chunks.jsonl"] = payload
    if system_prompt:
        files["templates/system_prompt.txt"] = system_prompt.encode("utf-8")
    if few_shot:
        files["templates/few_shot_examples.jsonl"] = "\n".join(json.dumps(x, ensure_ascii=False) for x in few_shot).encode("utf-8")
    if tools:
        files["tools/tools.yaml"] = json.dumps(tools).encode("utf-8")
    if tests:
        files["tests/benchmark.jsonl"] = "\n".join(json.dumps(x, ensure_ascii=False) for x in tests).encode("utf-8")
    return files


def write_adapter_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def extract_adapter_dir(apkg_path: Path, dest: Path | None = None) -> Path:
    import zipfile
    source = Path(apkg_path)
    if not zipfile.is_zipfile(source):
        raise ValueError(f"Not a zip archive: {source}")
    target = dest or source.parent / (source.stem + "_adapter")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as zf:
        for name in zf.namelist():
            if name.startswith("weights/"):
                out_path = target / Path(name).name
                out_path.write_bytes(zf.read(name))
    if not (target / "adapter_config.json").exists() and not (target / "adapter.safetensors").exists():
        raise ValueError(f"No adapter artifacts found in {source}")
    return target
