"""Benchmark validator that evaluates a module on test questions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class BenchmarkResult:
    score: float
    total: int
    passed: int
    details: List[dict]


def run_benchmark(module_path: Path, test_file: Path, generate_fn) -> BenchmarkResult:
    questions = []
    if test_file.exists():
        for line in test_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                questions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    passed = 0
    details = []
    for q in questions:
        prompt = q.get("input") or q.get("question", "")
        expected = q.get("expected") or q.get("answer", "")
        if not prompt:
            continue
        resp = generate_fn(prompt)
        text = resp.text if hasattr(resp, "text") else str(resp)
        ok = bool(expected) and (expected.lower() in text.lower())
        if ok:
            passed += 1
        details.append({"prompt": prompt, "expected": expected, "actual": text, "passed": ok})
    total = len(details)
    score = passed / total if total else 0.0
    return BenchmarkResult(score=score, total=total, passed=passed, details=details)
