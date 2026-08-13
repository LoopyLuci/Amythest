"""Integration tests for the FastAPI backend."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from amythest.backend.server import app

client = TestClient(app)


def test_status_endpoint():
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert "active_count" in body


def test_modules_list():
    r = client.get("/modules")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_hitl_queue_empty():
    r = client.get("/hitl/queue")
    assert r.status_code == 200
    assert r.json() == []


def test_hitl_evaluate_and_approve():
    r = client.post("/hitl/evaluate", json={"action": "tool_call", "description": "test action"})
    assert r.status_code == 200
    item = r.json()
    assert item["decided"] is False
    request_id = item["id"]
    r2 = client.post(f"/hitl/{request_id}/approve")
    assert r2.status_code == 200
    assert r2.json()["decision"] == "approved"
