"""Core module manager: install, load, unload, compose, and resolve conflicts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from amythest.storage.database import ModuleDatabase, StoredModule
from amythest.types import ModuleManifest, ModuleType
from amythest.package import ApkgError, read_apkg, write_apkg
from amythest.core.analyzer import TaskAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class ConflictReport:
    module_a: str
    module_b: str
    reason: str


class ModuleManager:
    def __init__(self, db: ModuleDatabase, index_path: Optional[Path] = None) -> None:
        self.db = db
        self.analyzer = TaskAnalyzer(index_path=index_path)

    def install_package(self, source: Path) -> StoredModule:
        logger.info("Installing module package: %s", source)
        package = read_apkg(source)
        manifest: ModuleManifest = package["manifest"]
        stored = self.db.install(manifest, source)
        logger.info(
            "Installed module %s %s at %s",
            manifest.name,
            manifest.version,
            stored.path,
        )
        return stored

    def uninstall(self, name: str, version: str) -> None:
        stored = self.db.get(name, version)
        if not stored:
            raise KeyError(f"Module not found: {name}=={version}")
        if stored.active:
            raise RuntimeError(f"Cannot uninstall active module: {name}=={version}")
        # remove file
        try:
            stored.path.unlink()
        except FileNotFoundError:
            pass
        with self.db._connect() as conn:
            conn.execute(
                "DELETE FROM modules WHERE name = ? AND version = ?",
                (name, version),
            )
        logger.info("Uninstalled module %s==%s", name, version)

    def activate(self, name: str, version: str, context: Optional[str] = None) -> StoredModule:
        stored = self.db.get(name, version)
        if not stored:
            raise KeyError(f"Module not found: {name}=={version}")
        active = [m for m in self.db.list_modules() if m.active]
        conflicts = self._detect_conflicts(stored.manifest, [m.manifest for m in active])
        if conflicts:
            reasons = "; ".join(f"{c.module_a} <-> {c.module_b}: {c.reason}" for c in conflicts)
            raise RuntimeError(f"Activation conflicts detected: {reasons}")
        self.db.activate(name, version, context=context)
        logger.info("Activated module %s==%s", name, version)
        return self.db.get(name, version)

    def deactivate(self, name: str, version: str) -> StoredModule:
        stored = self.db.get(name, version)
        if not stored:
            raise KeyError(f"Module not found: {name}=={version}")
        self.db.deactivate(name, version)
        logger.info("Deactivated module %s==%s", name, version)
        return self.db.get(name, version)

    def active_modules(self) -> List[StoredModule]:
        return [m for m in self.db.list_modules() if m.active]

    def discover(self, query: str = "") -> List[StoredModule]:
        modules = self.db.list_modules()
        if not query:
            return modules
        q = query.lower()
        return [
            m
            for m in modules
            if q in m.manifest.name.lower()
            or q in m.manifest.description.lower()
            or q in " ".join(m.manifest.tags).lower()
        ]

    def create_package(
        self,
        manifest: ModuleManifest,
        files: Optional[Dict[str, bytes]] = None,
        destination: Optional[Path] = None,
    ) -> Path:
        files = files or {}
        if destination is None:
            destination = Path(".") / f"{manifest.name}-{manifest.version}.apkg"
        return write_apkg(destination, manifest, files)

    def compose(self) -> Dict[str, object]:
        active = self.active_modules()
        return {
            "active_count": len(active),
            "active_modules": [
                {
                    "name": m.manifest.name,
                    "version": m.manifest.version,
                    "type": m.manifest.module_type.value,
                    "tags": m.manifest.tags,
                    "injection_ports": m.manifest.injection_ports,
                    "last_activated_at": m.last_activated_at.isoformat() if m.last_activated_at else None,
                }
                for m in active
            ],
        }

    def recommend_modules(self, description: str, top_k: int = 5) -> List[ModuleRecommendation]:
        modules = self.db.list_modules()
        task = Task(description=description)
        return self.analyzer.recommend(task, modules, top_k=top_k)

    def _detect_conflicts(self, candidate: ModuleManifest, active: Iterable[ModuleManifest]) -> List[ConflictReport]:
        reports: List[ConflictReport] = []
        dep_names = {d["name"] for d in candidate.dependencies}
        for existing in active:
            if existing.name == candidate.name:
                continue
            # tag clash heuristic
            shared_tags = set(candidate.tags) & set(existing.tags)
            if shared_tags and candidate.base_model_name != existing.base_model_name:
                reports.append(
                    ConflictReport(
                        module_a=f"{candidate.name}=={candidate.version}",
                        module_b=f"{existing.name}=={existing.version}",
                        reason=f"Shared tags but different base models: {sorted(shared_tags)}",
                    )
                )
            # dependency mismatch
            if existing.name in dep_names:
                dep_spec = next((d for d in candidate.dependencies if d["name"] == existing.name), None)
                if dep_spec:
                    reports.append(
                        ConflictReport(
                            module_a=f"{candidate.name}=={candidate.version}",
                            module_b=f"{existing.name}=={existing.version}",
                            reason=f"Requires {dep_spec['name']} {dep_spec['version']}",
                        )
                    )
        return reports
