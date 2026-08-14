"""Example datasets and module generation for Amythest."""

from __future__ import annotations

import json


def python_knowledge_text() -> str:
    return "\n".join([
        "Python 3.12 introduces new language features.",
        "Use asyncio.TaskGroup for structured concurrency.",
        "The 'type' statement enables clean aliases in Python 3.12.",
        "Pathlib is part of the standard library.",
        "Dataclasses provide class defaults with less boilerplate.",
        "The walrus operator ':=' enables assignment expressions.",
        "Context variables replace thread-local storage in asyncio.",
        "Exception groups and 'except*' handle multiple failures.",
    ])


def agent_skill_text() -> str:
    return "\n".join([
        "When using tools, always verify inputs before execution.",
        "Prefer readonly inspection before mutation.",
        "Report blockers honestly instead of fabricating results.",
        "Use rich markdown and explicit artifact paths for outputs.",
        "For long outputs, paginate or summarize rather than dump.",
    ])


def knowledge_module_files() -> dict[str, bytes]:
    chunks = [line for line in python_knowledge_text().splitlines() if line.strip()]
    payload = "\n".join(chunks).encode("utf-8")
    return {
        "chunks.jsonl": payload,
        "index/chunks.jsonl": payload,
    }


def skill_module_files() -> dict[str, bytes]:
    chunks = [line for line in agent_skill_text().splitlines() if line.strip()]
    examples = "\n".join(
        json.dumps({"input": chunk[:20], "expected": chunk}) for chunk in chunks
    )
    return {
        "few_shot_examples.jsonl": examples.encode("utf-8"),
        "templates/system_prompt.txt": (
            b"You are Amythest's agentic runtime. Follow these principles:\n"
        ) + agent_skill_text().encode("utf-8"),
    }
