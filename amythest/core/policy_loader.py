"""HITL policy loader."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import List

from amythest.core.hitl import Policy, ActionType


def load_policies(path: Path) -> List[Policy]:
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
