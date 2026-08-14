"""HITL policy loader."""
from __future__ import annotations

from pathlib import Path

import yaml

from amythest.core.hitl import ActionType, Policy


def load_policies(path: Path) -> list[Policy]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    policies = []
    for item in data:
        policies.append(Policy(
            action=ActionType(item["action"]),
            auto_approve=bool(item.get("auto_approve", False)),
            require_reason=bool(item.get("require_reason", False)),
            max_retries=int(item.get("max_retries", 2)),
        ))
    return policies
