"""Updated Amythest TUI with swarm graph, HITL pane, and shortcuts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    Timer,
)

from amythest.core.hitl import HITLEngine
from amythest.core.manager import ModuleManager
from amythest.storage.database import ModuleDatabase
from amythest.tui.swarm_graph import SwarmGraph


class LeftPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Modules", classes="panel_title")
        yield DataTable(id="modules_table")


class CenterPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Agent Stream", classes="panel_title")
        yield RichLog(id="agent_log", wrap=True)


class RightPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Metrics", classes="panel_title")
        yield Static("GPU: --", id="gpu_metric")
        yield Static("Active modules: 0", id="module_metric")
        yield Static("Uptime: 0s", id="uptime_metric")
        yield Static("Selected module: --", id="selected_module_metric")


class BottomPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("HITL Queue", classes="panel_title")
        yield DataTable(id="hitl_table")


class SwarmPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Swarm Status", classes="panel_title")
        yield SwarmGraph(id="swarm_graph")


class AmythestApp(App):
    CSS = """
    Screen { layout: vertical; }
    .columns { height: 1fr; }
    LeftPanel, CenterPanel, RightPanel, SwarmPanel {
      width: 1fr;
      border: solid $primary;
      padding: 1;
    }
    BottomPanel { height: 10; border: solid $primary; padding: 1; }
    Input { dock: bottom; margin: 1; }
    DataTable, RichLog { height: 1fr; }
    .panel_title { text-style: bold; color: $accent; dock: top; }
    """
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("l", "refresh_modules", "Refresh modules"),
        Binding("a", "activate_selected", "Activate selected"),
        Binding("d", "deactivate_selected", "Deactivate selected"),
        Binding("p", "pause_selected", "Pause agent"),
        Binding("r", "resume_selected", "Resume agent"),
        Binding("k", "kill_selected", "Kill agent"),
        Binding("/", "focus_input", "Command input"),
        Binding("1", "show_modules", "Modules"),
        Binding("2", "show_hitl", "HITL"),
        Binding("h", "approve_hitl", "Approve HITL"),
        Binding("j", "reject_hitl", "Reject HITL"),
        Binding("m", "modify_hitl", "Modify HITL"),
    ]

    command_text: reactive[str] = reactive("")
    started_at: datetime = datetime.now(UTC)
    swarm_agents: ClassVar[list[dict]] = []
    swarm_tasks: ClassVar[list[dict]] = []

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__()
        if db_path is None:
            db_path = Path.home() / ".amythest" / "modules"
        self.db = ModuleDatabase(db_path)
        self.manager = ModuleManager(self.db)
        self.hitl = HITLEngine()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(classes="columns"):
            yield SwarmPanel()
            yield LeftPanel()
            yield CenterPanel()
            yield RightPanel()
        yield BottomPanel()
        yield Input(placeholder="/command or search modules...", id="command_input")
        yield Timer(2, name="refresh_timer")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#modules_table", DataTable)
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Type")
        table.add_column("Active")
        self.refresh_modules()
        self.refresh_hitl()
        self.query_one(RichLog).write("[green]Amythest runtime initialized.[/green]")
        self.swarm_agents = [{"id": "a1", "status": "idle"}, {"id": "a2", "status": "busy"}, {"id": "a3", "status": "idle"}]
        self.swarm_tasks = [{"id": "t1", "status": "queued"}, {"id": "t2", "status": "running"}, {"id": "t3", "status": "done"}]
        graph = self.query_one("#swarm_graph", SwarmGraph)
        graph.update_data(self.swarm_agents, self.swarm_tasks)

    def refresh_modules(self) -> None:
        table = self.query_one("#modules_table", DataTable)
        table.clear()
        for m in self.manager.db.list_modules():
            table.add_row(
                m.manifest.name,
                m.manifest.version,
                m.manifest.module_type.value,
                "✓" if m.active else "✗",
            )
        self.query_one("#module_metric", Static).update(
            f"Active modules: {len(self.manager.active_modules())}"
        )
        self._update_selected_module()

    def _update_selected_module(self) -> None:
        table = self.query_one("#modules_table", DataTable)
        if table.cursor_coordinate.row is None:
            self.query_one("#selected_module_metric", Static).update("Selected module: --")
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        row = table.get_row(row_key)
        self.query_one("#selected_module_metric", Static).update(f"Selected module: {row[0]} {row[1]}")

    def refresh_hitl(self) -> None:
        table = self.query_one("#hitl_table", DataTable)
        table.clear()
        table.add_column("ID")
        table.add_column("Action")
        table.add_column("Description")
        for req in self.hitl.queue:
            table.add_row(req.id, req.action.value, req.description)

    def action_refresh_modules(self) -> None:
        self.refresh_modules()
        self.query_one(RichLog).write("[green]Module list refreshed.[/green]")

    def action_activate_selected(self) -> None:
        table = self.query_one("#modules_table", DataTable)
        if table.cursor_coordinate.row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        row = table.get_row(row_key)
        name, version, _module_type, active = row
        if active == "✓":
            self.query_one(RichLog).write(f"[yellow]Module already active: {name} {version}[/yellow]")
            return
        try:
            self.manager.activate(name, version, context="tui")
        except RuntimeError as exc:
            self.query_one(RichLog).write(f"[red]Activation failed: {exc}[/red]")
            return
        self.refresh_modules()
        self.query_one(RichLog).write(f"[green]Activated: {name} {version}[/green]")

    def action_deactivate_selected(self) -> None:
        table = self.query_one("#modules_table", DataTable)
        if table.cursor_coordinate.row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        row = table.get_row(row_key)
        name, version, _module_type, active = row
        if active == "✗":
            self.query_one(RichLog).write(f"[yellow]Module already inactive: {name} {version}[/yellow]")
            return
        try:
            self.manager.deactivate(name, version)
        except RuntimeError as exc:
            self.query_one(RichLog).write(f"[red]Deactivation failed: {exc}[/red]")
            return
        self.refresh_modules()
        self.query_one(RichLog).write(f"[yellow]Deactivated: {name} {version}[/yellow]")

    def action_pause_selected(self) -> None:
        self.query_one(RichLog).write("[yellow]Pause signal sent.[/yellow]")

    def action_resume_selected(self) -> None:
        self.query_one(RichLog).write("[green]Resume signal sent.[/green]")

    def action_kill_selected(self) -> None:
        self.query_one(RichLog).write("[red]Kill signal sent.[/red]")

    def action_focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    def on_timer(self, event: Timer) -> None:
        self.refresh_modules()
        self.refresh_hitl()

    def _selected_hitl_id(self) -> str | None:
        table = self.query_one("#hitl_table", DataTable)
        if table.cursor_coordinate.row is None:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(table.get_row(row_key)[0])

    def _apply_hitl_action(self, action: str) -> None:
        hitl_id = self._selected_hitl_id()
        log = self.query_one(RichLog)
        if not hitl_id:
            log.write("[yellow]No HITL item selected.[/yellow]")
            return
        try:
            self.hitl.decide(hitl_id, action, "tui")
            log.write(f"[green]HITL {hitl_id}: {action} recorded.[/green]")
            self.refresh_hitl()
        except Exception as exc:
            log.write(f"[red]HITL action failed: {exc}[/red]")

    def action_approve_hitl(self) -> None:
        self._apply_hitl_action("approve")

    def action_reject_hitl(self) -> None:
        self._apply_hitl_action("reject")

    def action_modify_hitl(self) -> None:
        hitl_id = self._selected_hitl_id()
        if not hitl_id:
            self.query_one(RichLog).write("[yellow]No HITL item selected.[/yellow]")
            return
        self.query_one(Input).value = f"/hitl modify {hitl_id} "
        self.action_focus_input()

    def action_show_modules(self) -> None:
        self.query_one(LeftPanel).remove_class("hidden")
        self.query_one(BottomPanel).remove_class("hidden")

    def action_show_hitl(self) -> None:
        self.refresh_hitl()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self.query_one(RichLog).write(f"[bold]$ {text}[/bold]")
        if text.startswith("/"):
            self.handle_command(text[1:].strip())

    def handle_command(self, raw: str) -> None:
        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]
        log = self.query_one(RichLog)
        if cmd == "list":
            self.refresh_modules()
            log.write("[green]Modules refreshed.[/green]")
        elif cmd == "status":
            log.write(json.dumps(self.manager.compose()))
        elif cmd == "doctor":
            missing = [m for m in self.manager.db.list_modules() if not m.path.exists()]
            log.write(f"Installed: {len(self.manager.db.list_modules())}; missing: {len(missing)}")
        elif cmd == "help":
            log.write("Commands: list, status, doctor, help, activate <name> <version>, deactivate <name> <version>")
        elif cmd == "activate" and len(args) == 2:
            try:
                self.manager.activate(args[0], args[1], context="tui")
                self.refresh_modules()
                log.write(f"[green]Activated {args[0]} {args[1]}[/green]")
            except RuntimeError as exc:
                log.write(f"[red]{exc}[/red]")
        elif cmd == "deactivate" and len(args) == 2:
            try:
                self.manager.deactivate(args[0], args[1])
                self.refresh_modules()
                log.write(f"[yellow]Deactivated {args[0]} {args[1]}[/yellow]")
            except RuntimeError as exc:
                log.write(f"[red]{exc}[/red]")
        elif cmd == "hitl" and len(args) >= 2:
            hitl_id = args[0]
            sub = args[1].lower()
            reason = " ".join(args[2:]) or "tui"
            try:
                self.hitl.decide(hitl_id, sub, reason)
                log.write(f"[green]HITL {hitl_id}: {sub} recorded.[/green]")
                self.refresh_hitl()
            except Exception as exc:
                log.write(f"[red]{exc}[/red]")
        else:
            log.write(f"[red]Unknown command: {cmd}[/red]")


def run(db_path: Path | None = None) -> None:
    AmythestApp(db_path=db_path).run()
