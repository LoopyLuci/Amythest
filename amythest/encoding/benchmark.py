"""Simple benchmark for module activation latency."""

from __future__ import annotations

import time
from pathlib import Path

from amythest.core.manager import ModuleManager
from amythest.storage.database import ModuleDatabase


def benchmark_activation_latency(iterations: int = 20) -> dict:
    db = ModuleDatabase(Path.home() / ".amythest" / "modules")
    manager = ModuleManager(db)
    modules = db.list_modules()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        for m in modules:
            try:
                manager.activate(m.manifest.name, m.manifest.version, context="benchmark")
            except RuntimeError:
                pass
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
    return {
        "iterations": iterations,
        "samples": samples,
        "min": min(samples),
        "max": max(samples),
        "mean": sum(samples) / len(samples),
    }


if __name__ == "__main__":
    print(benchmark_activation_latency())
