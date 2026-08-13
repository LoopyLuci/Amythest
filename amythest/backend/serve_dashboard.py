"""Build and serve the Amythest web dashboard from FastAPI static files."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from amythest.backend.server import app
from amythest.storage.database import ModuleDatabase
from amythest.core.manager import ModuleManager
from amythest.core.hitl import HITLEngine
from pathlib import Path

static_dir = Path(__file__).resolve().parent.parent / "web" / "out"
web_dir = Path(__file__).resolve().parent.parent / "web"


def build_dashboard() -> Path:
    if not web_dir.exists():
        raise RuntimeError(f"Web directory not found: {web_dir}")
    result = subprocess.run(["npm.cmd", "run", "build"], cwd=web_dir, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        raise RuntimeError(f"npm build failed: {result.stderr}")
    return static_dir


def serve_dashboard(host: str = "127.0.0.1", port: int = 8125, static_path: Path = None) -> None:
    from fastapi.staticfiles import StaticFiles
    from uvicorn import Config, Server

    if static_path is None:
        static_path = build_dashboard()
    if not static_path.exists():
        raise RuntimeError(f"Static files not found at {static_path}. Run build first.")

    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="web")
    db = ModuleDatabase(Path.home() / ".amythest" / "modules")
    index_path = Path.home() / ".amythest" / "modules" / "module_index.db"
    ModuleManager(db, index_path=index_path)
    HITLEngine()

    config = Config(app=app, host=host, port=port, log_level="info")
    server = Server(config)
    print(f"Serving dashboard at http://{host}:{port}")
    server.run()


if __name__ == "__main__":
    serve_dashboard()
