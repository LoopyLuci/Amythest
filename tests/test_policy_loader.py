"""Tests for HITL policy loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from amythest.core.hitl import ActionType, Policy
from amythest.core.policy_loader import load_policies


def test_load_default_policies() -> None:
    policies = load_policies(Path("amythest/policies/default.yaml"))
    assert any(p.action == ActionType.EXTERNAL_REQUEST and p.auto_approve for p in policies)
    assert any(p.action == ActionType.MODEL_EDIT and p.require_reason for p in policies)


def test_missing_policies_returns_empty() -> None:
    assert load_policies(Path("does_not_exist.yaml")) == []
