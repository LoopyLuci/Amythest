"""Atomic checkpoint and hot-reload for Amythest runtime."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Checkpoint:
    path: Path
    created_at: datetime = field(default_factory=datetime.utcnow)
    active_modules: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


class CheckpointManager:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, active_modules: List[str], metadata: Optional[Dict[str, object]] = None, model_state: Optional[ModelState] = None, adapter_shards: Optional[List[str]] = None) -> Checkpoint:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dest = self.root / f"checkpoint-{stamp}"
        dest.mkdir(parents=True, exist_ok=False)
        manifest = {
            "active_modules": active_modules,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "model": {
                "name": model_state.model_name if model_state else "",
                "weight_hash": model_state.weight_hash if model_state else "",
                "device": model_state.device if model_state else "",
            },
            "adapter_shards": adapter_shards or [],
        }
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return Checkpoint(path=dest, active_modules=active_modules, metadata=metadata or {})

    def latest(self) -> Optional[Checkpoint]:
        candidates = sorted(self.root.glob("checkpoint-*"), reverse=True)
        if not candidates:
            return None
        return self._load(candidates[0])

    def rollback(self, checkpoint: Optional[Checkpoint] = None) -> Checkpoint:
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


class HotReloadWatcher:
    def __init__(self, paths: List[Path], on_change) -> None:
        self.paths = paths
        self.on_change = on_change
