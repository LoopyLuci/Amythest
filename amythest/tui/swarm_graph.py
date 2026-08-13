"""Minimal swarm graph widget for Amythest TUI."""

from __future__ import annotations

from textual.widgets import Static


class SwarmGraph(Static):
    def render(self) -> str:
        agents = getattr(self, "agents", []) or []
        tasks = getattr(self, "tasks", []) or []
        lines = ["Swarm", "─────"]
        for a in agents[:8]:
            status = getattr(a, "status", "idle")
            label = getattr(a, "label", str(a))
            marker = {"running": "▶", "paused": "⏸", "failed": "✗", "done": "✓"}.get(status, "·")
            lines.append(f"{marker} {label}")
        if tasks:
            lines.append("Tasks")
            lines.append("─────")
            for t in tasks[:8]:
                name = getattr(t, "name", str(t))
                state = getattr(t, "state", "queued")
                lines.append(f"- {name}: {state}")
        return "\n".join(lines) if len(lines) > 2 else "Swarm\n─────\n(empty)"
