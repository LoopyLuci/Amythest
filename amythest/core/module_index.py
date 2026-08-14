"""Semantic module selection using local FAISS index."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from amythest.core.analyzer import ModuleRecommendation, Task


@dataclass(frozen=True)
class ModuleIndex:
    db_path: Path
    dim: int = 384

    def index_path(self) -> Path:
        return self.db_path.with_suffix(".faiss")

    def build(self, modules: Sequence[object]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        texts = []
        for idx, m in enumerate(modules):
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
            text = f"{name} {desc} {' '.join(tags)}"
            texts.append(text)
            rows.append((idx, name, version, text, datetime.now(UTC).isoformat()))
        embeddings = _embed(texts)
        import faiss
        index = faiss.IndexFlatL2(self.dim)
        index.add(embeddings)
        faiss.write_index(index, str(self.index_path()))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, version TEXT, text TEXT, indexed_at TEXT)")
            conn.execute("DELETE FROM items")
            conn.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?)", rows)

    def search(self, task: Task, top_k: int = 5) -> list[ModuleRecommendation]:
        if not self.index_path().exists():
            return []
        q = _embed([task.description])
        import faiss
        index = faiss.read_index(str(self.index_path()))
        scores, ids = index.search(q, min(top_k, index.ntotal))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, name, version, text FROM items WHERE id IN (" + ",".join("?" for _ in ids[0]) + ")", [int(x) for x in ids[0]]).fetchall()
        by_id = {row[0]: row for row in rows}
        results = []
        for rank, idx in enumerate(ids[0]):
            if int(idx) < 0:
                continue
            row = by_id.get(int(idx))
            if not row:
                continue
            _row_id, name, version, _text = row
            results.append(ModuleRecommendation(name=name, version=version, score=float(scores[0][rank]), reason="Embedding similarity"))
        results.sort(key=lambda x: x.score)
        return results


def _embed(texts: Sequence[str]) -> np.ndarray:
    import numpy as np
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        vecs = model.encode(texts, normalize_embeddings=True)
        return np.array(vecs, dtype="float32")
    except RuntimeError:
        return np.zeros((len(texts), 384), dtype="float32")
