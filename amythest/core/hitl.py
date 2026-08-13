"""HITL policy engine and approval queue."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    MODEL_EDIT = "model_edit"
    MODULE_INSTALL = "module_install"
    MODULE_ACTIVATE = "module_activate"
    EXTERNAL_REQUEST = "external_request"


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass(frozen=True)
class Policy:
    action: ActionType
    auto_approve: bool = False
    require_reason: bool = False
    max_retries: int = 2


_DEFAULT_POLICIES = [
    Policy(action=ActionType.TOOL_CALL, auto_approve=False),
    Policy(action=ActionType.MODEL_EDIT, auto_approve=False, require_reason=True),
    Policy(action=ActionType.MODULE_INSTALL, auto_approve=False),
    Policy(action=ActionType.MODULE_ACTIVATE, auto_approve=False),
    Policy(action=ActionType.EXTERNAL_REQUEST, auto_approve=True),
]


@dataclass
class ApprovalRequest:
    id: str
    action: ActionType
    description: str
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    decided: bool = False
    decision: Optional[Decision] = None
    modifier: Optional[str] = None


class HITLEngine:
    def __init__(self, policies: Optional[List[Policy]] = None) -> None:
        self.policies = {p.action: p for p in (policies or _DEFAULT_POLICIES)}
        self.queue: List[ApprovalRequest] = []
        self.history: List[ApprovalRequest] = []

    def evaluate(self, action: ActionType, description: str, payload: Optional[dict] = None) -> ApprovalRequest:
        policy = self.policies.get(action)
        req = ApprovalRequest(
            id=_request_id(action, description),
            action=action,
            description=description,
            payload=payload or {},
        )
        if policy and policy.auto_approve:
            req.decided = True
            req.decision = Decision.APPROVED
            self.history.append(req)
            return req
        self.queue.append(req)
        return req

    def approve(self, request_id: str) -> Optional[ApprovalRequest]:
        return _decide(self.queue, self.history, request_id, Decision.APPROVED)

    def reject(self, request_id: str) -> Optional[ApprovalRequest]:
        return _decide(self.queue, self.history, request_id, Decision.REJECTED)

    def modify(self, request_id: str, modifier: str) -> Optional[ApprovalRequest]:
        req = _find(self.queue, request_id)
        if not req:
            return None
        req.decided = True
        req.decision = Decision.MODIFIED
        req.modifier = modifier
        self.queue.remove(req)
        self.history.append(req)
        return req


def _request_id(action: ActionType, description: str) -> str:
    stamp = datetime.utcnow().strftime("%H%M%S")
    return f"{action.value}-{stamp}-{hash(description) % 10000:04d}"


def _find(queue: List[ApprovalRequest], request_id: str) -> Optional[ApprovalRequest]:
    for req in queue:
        if req.id == request_id:
            return req
    return None


def _decide(queue: List[ApprovalRequest], history: List[ApprovalRequest], request_id: str, decision: Decision) -> Optional[ApprovalRequest]:
    req = _find(queue, request_id)
    if not req:
        return None
    req.decided = True
    req.decision = decision
    queue.remove(req)
    history.append(req)
    return req
