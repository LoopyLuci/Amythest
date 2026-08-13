"""Generate example Amythest modules for demonstration."""

from __future__ import annotations

from pathlib import Path

from amythest.core.manager import ModuleManager
from amythest.examples.builder import knowledge_module_files, skill_module_files
from amythest.package import write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType


def generate_examples(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    knowledge_manifest = ModuleManifest(
        name="python-3.12-knowledge",
        version="1.0.0",
        author="amythest-examples",
        description="Python 3.12 language knowledge snippets",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
        tags=["python", "programming", "stdlib"],
    )
    knowledge_path = write_apkg(output_dir / f"{knowledge_manifest.name}-{knowledge_manifest.version}.apkg", knowledge_manifest, knowledge_module_files())

    skill_manifest = ModuleManifest(
        name="agentic-runtime-skills",
        version="1.0.0",
        author="amythest-examples",
        description="Agent runtime behavioral skills",
        module_type=ModuleType.SKILL,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
        tags=["agents", "skills", "runtime"],
    )
    skill_path = write_apkg(output_dir / f"{skill_manifest.name}-{skill_manifest.version}.apkg", skill_manifest, skill_module_files())

    return knowledge_path, skill_path


def install_examples(db_root: Path, output_dir: Path) -> None:
    knowledge_path, skill_path = generate_examples(output_dir)
    db = ModuleDatabase(db_root)
    manager = ModuleManager(db)
    manager.install_package(knowledge_path)
    manager.install_package(skill_path)
    manager.activate("python-3.12-knowledge", "1.0.0", context="demo")
    manager.activate("agentic-runtime-skills", "1.0.0", context="demo")


if __name__ == "__main__":
    install_examples(
        Path.home() / ".amythest" / "modules",
        Path(__file__).resolve().parent.parent / "modules",
    )
