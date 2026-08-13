"""Task analyzer: recommend modules for a given task description."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class Task:
    description: str
    kind: str = "general"
    priority: str = "normal"
    context: Optional[str] = None


@dataclass(frozen=True)
class ModuleRecommendation:
    name: str
    version: str
    score: float
    reason: str


class TaskAnalyzer:
    def recommend(self, task: Task, modules: Sequence[object], top_k: int = 5) -> List[ModuleRecommendation]:
        scored: List[ModuleRecommendation] = []
        keywords = task.description.lower().split()
        for m in modules:
            if isinstance(m, dict):
                name = m.get("name", "")
                desc = m.get("description", "")
                tags = m.get("tags", [])
                version = m.get("version", "")
            else:
                name = getattr(m, "name", "")
                desc = getattr(m, "description", "")
                tags = getattr(m, "tags", [])
                version = getattr(m, "version", "")
            text = f"{name} {desc} {' '.join(tags)}".lower()
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                scored.append(ModuleRecommendation(name=name, version=version, score=float(score), reason="Keyword match"))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
