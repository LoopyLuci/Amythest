"""Generate a real example knowledge module from a small corpus."""

from __future__ import annotations

from pathlib import Path

from amythest.core.manager import ModuleManager
from amythest.encoding.pipeline import ingest_directory, ingest_text
from amythest.encoding.trainer import package_module_outputs, save_jsonl
from amythest.encoding.validator import validate_package
from amythest.package import write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType


def build_real_knowledge_module(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = [
        "Python 3.12 introduces the 'type' statement for type alias declarations.",
        "asyncio.TaskGroup provides structured concurrency for Python 3.12+.",
        "Exception groups allow raising and handling multiple exceptions simultaneously.",
        "The 'except*' syntax is used for handling exception groups.",
        "f-strings now support = for debugging in Python 3.12.",
        "Pathlib is part of the Python standard library for filesystem paths.",
        "The walrus operator ':=' enables assignment expressions inside expressions.",
        "Context variables replace thread-local storage in asyncio code.",
    ]
    manifest = ModuleManifest(
        name="python-3.12-knowledge",
        version="1.1.0",
        author="amythest-examples",
        description="Python 3.12 standard library and language feature knowledge",
        module_type=ModuleType.KNOWLEDGE,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
        tags=["python", "programming", "stdlib", "language"],
        benchmark_score=0.92,
    )
    records = [{"question": f"What is {chunks[i].split()[0]}?", "answer": chunks[i]} for i in range(min(3, len(chunks)))]
    save_jsonl(records, output_dir / "tests" / "benchmark.jsonl")
    files = package_module_outputs(
        manifest_path=output_dir / "manifest.json",
        chunks=chunks,
        tests=records,
    )
    dest = write_apkg(output_dir / f"{manifest.name}-{manifest.version}.apkg", manifest, files)
    return dest


def build_real_skill_module(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts = [
        "When using tools, always verify inputs before execution.",
        "Prefer readonly inspection before mutation.",
        "Report blockers honestly instead of fabricating results.",
        "Use rich markdown and explicit artifact paths for outputs.",
        "For long outputs, paginate or summarize rather than dump.",
    ]
    manifest = ModuleManifest(
        name="agentic-runtime-skills",
        version="1.1.0",
        author="amythest-examples",
        description="Agent runtime behavioral skills and operational guardrails",
        module_type=ModuleType.SKILL,
        base_model_name="amythest-base",
        base_model_version="0.1.0",
        base_model_architecture="dense-70b",
        tags=["agents", "skills", "runtime"],
        benchmark_score=0.88,
    )
    files = package_module_outputs(
        manifest_path=output_dir / "manifest.json",
        system_prompt="You are Amythest's agentic runtime.\n" + "\n".join(prompts),
        few_shot=[{"input": p[:20], "expected": p} for p in prompts],
        tests=[{"input": "tool use", "expected": "verify inputs"}],
    )
    dest = write_apkg(output_dir / f"{manifest.name}-{manifest.version}.apkg", manifest, files)
    return dest


def install_real_examples(db_root: Path, output_dir: Path) -> None:
    kp = build_real_knowledge_module(output_dir)
    sp = build_real_skill_module(output_dir)
    db = ModuleDatabase(db_root)
    mgr = ModuleManager(db)
    mgr.install_package(kp)
    mgr.install_package(sp)
    mgr.activate("python-3.12-knowledge", "1.1.0", context="real")
    mgr.activate("agentic-runtime-skills", "1.1.0", context="real")


if __name__ == "__main__":
    install_real_examples(
        Path.home() / ".amythest" / "modules",
        Path(__file__).resolve().parent.parent / "modules",
    )
