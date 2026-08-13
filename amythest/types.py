"""Core domain types and module manifest schema."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class ModuleType(str, Enum):
    KNOWLEDGE = "knowledge"
    SKILL = "skill"
    PERSONALITY = "personality"
    TOOL = "tool"
    LANGUAGE = "language"
    COMPOSITE = "composite"


@dataclass(frozen=True)
class ModuleManifest:
    """Manifest for an Amythest module package (.apkg)."""

    name: str
    version: str
    author: str
    description: str
    module_type: ModuleType

    base_model_name: str
    base_model_version: str
    base_model_architecture: str

    dependencies: List[Dict[str, str]] = field(default_factory=list)
    injection_ports: List[int] = field(default_factory=lambda: [0, 4, 8, 12])
    size_mb: float = 0.0
    tags: List[str] = field(default_factory=list)
    benchmark_score: Optional[float] = None
    sha256: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "version": self.version,
                "author": self.author,
                "description": self.description,
                "type": self.module_type.value,
                "base_model": {
                    "name": self.base_model_name,
                    "version": self.base_model_version,
                    "architecture": self.base_model_architecture,
                },
                "dependencies": self.dependencies,
                "injection_ports": self.injection_ports,
                "size_mb": self.size_mb,
                "tags": self.tags,
                "benchmark_score": self.benchmark_score,
                "sha256": self.sha256,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str) -> "ModuleManifest":
        payload = json.loads(data)
        return cls(
            name=payload["name"],
            version=payload["version"],
            author=payload["author"],
            description=payload["description"],
            module_type=ModuleType(payload["type"]),
            base_model_name=payload["base_model"]["name"],
            base_model_version=payload["base_model"]["version"],
            base_model_architecture=payload["base_model"]["architecture"],
            dependencies=payload.get("dependencies", []),
            injection_ports=payload.get("injection_ports", [0, 4, 8, 12]),
            size_mb=payload.get("size_mb", 0.0),
            tags=payload.get("tags", []),
            benchmark_score=payload.get("benchmark_score"),
            sha256=payload.get("sha256"),
        )

    def validate_against_base(self, current_model: str) -> bool:
        return current_model == self.base_model_name
