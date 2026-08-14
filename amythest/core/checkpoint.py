from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

__all__ = ["Checkpoint", "CheckpointManager"]


@dataclass
class Checkpoint:
    path: Path
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    active_modules: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class CheckpointManager:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, active_modules: list[str], metadata: dict[str, object] | None = None, model_state: object | None = None, adapter_shards: list[str] | None = None) -> Checkpoint:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        dest = self.root / f"checkpoint-{stamp}"
        dest.mkdir(parents=True, exist_ok=False)
        manifest = {
            "active_modules": active_modules,
            "metadata": metadata or {},
            "created_at": datetime.now(UTC).isoformat(),
            "model": {
                "name": getattr(model_state, "model_name", "") if model_state else "",
                "weight_hash": getattr(model_state, "weight_hash", "") if model_state else "",
                "device": getattr(model_state, "device", "") if model_state else "",
            },
            "adapter_shards": adapter_shards or [],
        }
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return Checkpoint(path=dest, active_modules=active_modules, metadata=metadata or {})

    def latest(self) -> Checkpoint | None:
        candidates = sorted(self.root.glob("checkpoint-*"), reverse=True)
        if not candidates:
            return None
        return self._load(candidates[0])

    def rollback(self, checkpoint: Checkpoint | None = None) -> Checkpoint:
        target = checkpoint or self.latest()
        if not target:
            raise RuntimeError("No checkpoint available for rollback.")
        raw = json.loads((target.path / "manifest.json").read_text(encoding="utf-8"))
        target.active_modules = raw.get("active_modules", [])
        target.metadata = raw.get("metadata", {})
        return target

    def _load(self, path: Path) -> Checkpoint:
        raw = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        return Checkpoint(path=path, active_modules=raw.get("active_modules", []), metadata=raw.get("metadata", {}))
