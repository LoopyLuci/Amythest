"""Task analyzer: recommend modules for a given task description."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    def __init__(self, index_path: Optional[Path] = None) -> None:
        self.index_path = index_path

    def recommend(self, task: Task, modules: Sequence[object], top_k: int = 5) -> List[ModuleRecommendation]:
        semantic = self._semantic_recommend(task, modules, top_k=top_k)
        if semantic:
            return semantic
        return self._keyword_recommend(task, modules, top_k=top_k)

    def _semantic_recommend(self, task: Task, modules: Sequence[object], top_k: int = 5) -> List[ModuleRecommendation]:
        if not self.index_path or not self.index_path.exists():
            return []
        try:
            from amythest.core.module_index import ModuleIndex
            index = ModuleIndex(self.index_path)
            results = index.search(task, top_k=top_k)
            if results:
                return results
        except Exception:
            return []
        return []

    def _keyword_recommend(self, task: Task, modules: Sequence[object], top_k: int = 5) -> List[ModuleRecommendation]:
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
            scored.append(ModuleRecommendation(name=name, version=version, score=float(score), reason="Keyword match"))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
