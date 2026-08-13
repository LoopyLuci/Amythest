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


def test_recommend_endpoint():
    r = client.post("/recommend", json={"description": "python asyncio", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    if body:
        assert "name" in body[0]
        assert "version" in body[0]


def test_usage_endpoints():
    r = client.post("/usage", json={"task_category": "qa", "module_name": "python-3.12-knowledge", "module_version": "1.0.0", "active": True, "helpful": True})
    assert r.status_code == 200
    r2 = client.get("/usage/rate?module_name=python-3.12-knowledge&module_version=1.0.0")
    assert r2.status_code == 200
    body = r2.json()
    assert body["module_name"] == "python-3.12-knowledge"
    assert body["helpful_rate"] == 1.0
