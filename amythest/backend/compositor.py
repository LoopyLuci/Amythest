"""Compose prompt/runtime context from active modules for inference."""

from __future__ import annotations


def compose_prompt(base_prompt: str, modules: list[dict]) -> str:
    parts: list[str] = []
    for m in modules:
        m_type = m.get("type", "")
        if m_type in {"knowledge", "composite"}:
            chunks = m.get("chunks") or []
            if chunks:
                parts.append("[MODULE KNOWLEDGE]\n" + "\n".join(chunks[:5]))
        if m_type in {"skill", "composite", "personality"}:
            prompt = m.get("system_prompt")
            if prompt:
                parts.append("[MODULE BEHAVIOR]\n" + prompt)
    parts.append("[USER QUERY]\n" + base_prompt)
    return "\n\n".join(parts)
