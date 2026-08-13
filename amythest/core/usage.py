"""Track module effectiveness for auto-selection and rollback."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class UsageRecord:
    task_category: str
    module_name: str
    module_version: str
    active: bool
    helpful: Optional[bool]
    timestamp: datetime


class UsageTracker:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_category TEXT NOT NULL,
                  module_name TEXT NOT NULL,
                  module_version TEXT NOT NULL,
                  active INTEGER NOT NULL,
                  helpful INTEGER,
                  timestamp TEXT NOT NULL
                )
                """
            )

    def record(self, record: UsageRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO usage (task_category, module_name, module_version, active, helpful, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.task_category,
                    record.module_name,
                    record.module_version,
                    1 if record.active else 0,
                    record.helpful,
                    record.timestamp.isoformat(),
                ),
            )

    def helpful_rate(self, module_name: str, module_version: str) -> Optional[float]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT helpful FROM usage WHERE module_name = ? AND module_version = ? AND helpful IS NOT NULL",
                (module_name, module_version),
            ).fetchall()
        if not rows:
            return None
        vals = [row["helpful"] for row in rows]
        return sum(vals) / len(vals)
