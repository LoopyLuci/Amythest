"""Dataset encoding pipeline stub: text -> chunks -> embeddings -> module content."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def chunk_text(text: str, size: int = 512, overlap: int = 64) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else len(text)
    return chunks


def ingest_text(path: Path, size: int = 512, overlap: int = 64) -> List[str]:
    return chunk_text(path.read_text(encoding="utf-8", errors="replace"), size=size, overlap=overlap)


def ingest_directory(root: Path, size: int = 512, overlap: int = 64) -> List[str]:
    chunks: List[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.suffix.lower() in {".py", ".md", ".txt", ".json", ".yaml", ".yml"}:
            try:
                chunks.extend(ingest_text(path, size=size, overlap=overlap))
            except Exception:
                continue
    return chunks


def build_knowledge_payload(chunks: Iterable[str]) -> dict:
    items = list(chunks)
    return {"chunk_count": len(items), "preview": "\n\n".join(items[:5])}
