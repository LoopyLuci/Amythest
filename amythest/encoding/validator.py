"""Validate module packages: conflicts, manifest, and benchmark."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from amythest.package import ApkgError, read_apkg
from amythest.types import ModuleManifest, ModuleType


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.benchmark_score: float | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_manifest(manifest: ModuleManifest, result: ValidationResult) -> None:
    if not manifest.name.strip():
        result.errors.append("Module name is empty.")
    if not manifest.description.strip():
        result.warnings.append("Module description is empty.")
    if manifest.version.count(".") != 2:
        result.warnings.append("Semantic version recommended: major.minor.patch.")
    if manifest.module_type not in ModuleType:
        result.errors.append(f"Unknown module type: {manifest.module_type}")
    if manifest.benchmark_score is not None:
        if not (0.0 <= manifest.benchmark_score <= 1.0):
            result.errors.append("benchmark_score must be between 0 and 1.")
        else:
            result.benchmark_score = manifest.benchmark_score


def validate_package(path: Path) -> ValidationResult:
    result = ValidationResult()
    try:
        package = read_apkg(path)
    except ApkgError as exc:
        result.errors.append(str(exc))
        return result
    manifest = package["manifest"]
    validate_manifest(manifest, result)
    if manifest.module_type == ModuleType.KNOWLEDGE and "index/chunks.jsonl" not in package["files"]:
        result.warnings.append("Knowledge modules should include an index/chunks.jsonl.")
    if manifest.module_type in {ModuleType.SKILL, ModuleType.PERSONALITY} and "templates/system_prompt.txt" not in package["files"]:
        result.warnings.append("Skill/personality modules usually include templates/system_prompt.txt.")
    if "tests/benchmark.jsonl" not in package["files"]:
        result.warnings.append("Missing tests/benchmark.jsonl.")
    return result


def detect_conflicts(modules: Iterable[ModuleManifest]) -> list[str]:
    items = list(modules)
    conflicts: list[str] = []
    seen: dict[str, str] = {}
    for m in items:
        key = m.name
        if key in seen:
            conflicts.append(f"Duplicate module name: {m.name} ({seen[key]} vs {m.version})")
        seen[key] = m.version
    return conflicts
