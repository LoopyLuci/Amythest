"""Verification script: start FastAPI server on a free port, exercise endpoints, stop server."""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path

import requests
from uvicorn import Config, Server

from amythest.backend.server import app
from amythest.core.hitl import HITLEngine
from amythest.core.manager import ModuleManager
from amythest.storage.database import ModuleDatabase


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def run_server(port: int) -> Server:
    db = ModuleDatabase(Path.home() / ".amythest" / "modules")
    ModuleManager(db)
    HITLEngine()
    config = Config(app=app, host="127.0.0.1", port=port, log_level="error")
    server = Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)
    return server


def wait_for_server(base: str, timeout: int = 10) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(base + "/status", timeout=1)
            return
        except requests.ConnectionError:
            time.sleep(0.25)
    raise RuntimeError(f"Server did not become ready at {base}")


def verify() -> dict:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    server = run_server(port)
    wait_for_server(base)
    results = {}
    try:
        results["status"] = requests.get(base + "/status").json()
        results["modules_count"] = len(requests.get(base + "/modules").json())
        results["hitl_queue"] = len(requests.get(base + "/hitl/queue").json())
        evaluate = requests.post(base + "/hitl/evaluate", json={"action": "tool_call", "description": "verify endpoint"}).json()
        results["evaluated"] = evaluate
        approve = requests.post(base + f"/hitl/{evaluate['id']}/approve").json()
        results["approved"] = approve
    finally:
        server.should_exit = True
        time.sleep(1)
    return results


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
