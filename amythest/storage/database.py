"""Local module library storage with SQLite + FAISS-backed discovery."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from amythest.types import ModuleManifest


@dataclass(frozen=True)
class StoredModule:
    manifest: ModuleManifest
    path: Path
    installed_at: datetime
    last_activated_at: datetime | None = None
    active: bool = False


class ModuleDatabase:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "modules.db"
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS modules (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  version TEXT NOT NULL,
                  module_type TEXT NOT NULL,
                  author TEXT NOT NULL,
                  description TEXT NOT NULL,
                  path TEXT NOT NULL,
                  active INTEGER NOT NULL DEFAULT 0,
                  last_activated_at TEXT,
                  installed_at TEXT NOT NULL,
                  manifest_json TEXT NOT NULL,
                  UNIQUE(name, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  module_name TEXT NOT NULL,
                  module_version TEXT NOT NULL,
                  activated_at TEXT NOT NULL,
                  context TEXT
                )
                """
            )

    def install(self, manifest: ModuleManifest, path: Path) -> StoredModule:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO modules
                  (name, version, module_type, author, description, path, active, installed_at, manifest_json)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    manifest.name,
                    manifest.version,
                    manifest.module_type.value,
                    manifest.author,
                    manifest.description,
                    str(path),
                    now,
                    manifest.to_json(),
                ),
            )
        return self.get(manifest.name, manifest.version)

    def get(self, name: str, version: str) -> StoredModule | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM modules WHERE name = ? AND version = ?",
                (name, version),
            ).fetchone()
        if not row:
            return None
        return self._row_to_module(row)

    def list_modules(self) -> list[StoredModule]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM modules ORDER BY name, version").fetchall()
        return [self._row_to_module(row) for row in rows]

    def activate(self, name: str, version: str, context: str | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE modules SET active = 1, last_activated_at = ? WHERE name = ? AND version = ?",
                (now, name, version),
            )
            conn.execute(
                "INSERT INTO activations (module_name, module_version, activated_at, context) VALUES (?, ?, ?, ?)",
                (name, version, now, context),
            )

    def deactivate(self, name: str, version: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE modules SET active = 0 WHERE name = ? AND version = ?",
                (name, version),
            )

    def _row_to_module(self, row: sqlite3.Row) -> StoredModule:
        manifest = ModuleManifest.from_json(row["manifest_json"])
        last = row["last_activated_at"]
        return StoredModule(
            manifest=manifest,
            path=Path(row["path"]),
            installed_at=datetime.fromisoformat(row["installed_at"]),
            last_activated_at=datetime.fromisoformat(last) if last else None,
            active=bool(row["active"]),
        )
