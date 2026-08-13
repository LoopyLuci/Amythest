"""Amythest CLI: create, install, activate, and inspect modules."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from amythest.core.manager import ModuleManager
from amythest.encoding.pipeline import build_knowledge_payload, ingest_directory, ingest_text
from amythest.package import write_apkg
from amythest.storage.database import ModuleDatabase
from amythest.types import ModuleManifest, ModuleType

console = Console()


def _default_db() -> ModuleDatabase:
    return ModuleDatabase(Path.home() / ".amythest" / "modules")


def _default_manager() -> ModuleManager:
    return ModuleManager(_default_db())


@click.group()
@click.version_option()
def main() -> None:
    """Amythest: modular scalable model architecture."""


@main.command()
@click.argument("source", type=click.Path(path_type=Path))
@click.option("--name", required=True)
@click.option("--version", default="0.1.0")
@click.option("--author", default="anonymous")
@click.option("--description", default="")
@click.option("--type", "module_type", default=ModuleType.KNOWLEDGE.value, type=click.Choice([e.value for e in ModuleType]))
@click.option("--base-model", default="amythest-base")
@click.option("--base-model-version", default="0.1.0")
@click.option("--base-model-architecture", default="dense-70b")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
def create(
    source: Path,
    name: str,
    version: str,
    author: str,
    description: str,
    module_type: str,
    base_model: str,
    base_model_version: str,
    base_model_architecture: str,
    output_path: Optional[Path],
) -> None:
    """Create a new .apkg module from SOURCE."""
    if not source.exists():
        raise click.ClickException(f"Source path does not exist: {source}")
    manifest = ModuleManifest(
        name=name,
        version=version,
        author=author,
        description=description,
        module_type=ModuleType(module_type),
        base_model_name=base_model,
        base_model_version=base_model_version,
        base_model_architecture=base_model_architecture,
    )
    files: dict[str, bytes] = {}
    if module_type == ModuleType.KNOWLEDGE.value:
        if source.is_dir():
            chunks = ingest_directory(source)
        else:
            chunks = ingest_text(source)
        payload = build_knowledge_payload(chunks)
        files["chunks.jsonl"] = "\n".join(chunks).encode("utf-8")
        files["index/chunks.jsonl"] = files["chunks.jsonl"]
        manifest.tags = list({chunk.split()[0] for chunk in chunks[:10] if chunk.strip()})[:5]
        manifest.size_mb = round(len(files["chunks.jsonl"]) / (1024 * 1024), 2)
    if output_path is None:
        output_path = Path.cwd() / f"{name}-{version}.apkg"
    dest = write_apkg(output_path, manifest, files)
    console.print(
        Panel.fit(
            f"[bold green]Created module package:[/bold green] {dest}\n"
            f"Name: {manifest.name}\nVersion: {manifest.version}\nType: {manifest.module_type.value}",
            title="Module Created",
        )
    )


@main.command()
@click.argument("package", type=click.Path(path_type=Path))
@click.option("--force", is_flag=True, help="Overwrite existing module if present.")
def install(package: Path, force: bool) -> None:
    """Install a .apkg module package."""
    manager = _default_manager()
    try:
        stored = manager.install_package(package)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        Panel.fit(
            f"[bold green]Installed:[/bold green] {stored.manifest.name} {stored.manifest.version}\n"
            f"Author: {stored.manifest.author}\nPath: {stored.path}",
            title="Module Installed",
        )
    )


@main.command()
@click.argument("name")
@click.argument("version")
@click.option("--context", default=None, help="Optional activation context description.")
def activate(name: str, version: str, context: Optional[str]) -> None:
    """Activate a module."""
    manager = _default_manager()
    try:
        stored = manager.activate(name, version, context=context)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        Panel.fit(
            f"[bold green]Activated:[/bold green] {stored.manifest.name} {stored.manifest.version}\n"
            f"Ports: {stored.manifest.injection_ports}",
            title="Module Activated",
        )
    )


@main.command()
@click.argument("name")
@click.argument("version")
def deactivate(name: str, version: str) -> None:
    """Deactivate an active module."""
    manager = _default_manager()
    try:
        stored = manager.deactivate(name, version)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        f"[yellow]Deactivated:[/yellow] {stored.manifest.name} {stored.manifest.version}"
    )


@main.command()
@click.argument("name")
@click.argument("version")
def uninstall(name: str, version: str) -> None:
    """Uninstall a module entirely."""
    manager = _default_manager()
    try:
        manager.uninstall(name, version)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(f"[red]Uninstalled:[/red] {name}=={version}")


@main.command("list")
def list_cmd() -> None:
    """List installed modules."""
    manager = _default_manager()
    modules = manager.db.list_modules()
    table = Table(title="Amythest Modules")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Type")
    table.add_column("Active")
    table.add_column("Size MB")
    for m in modules:
        table.add_row(
            m.manifest.name,
            m.manifest.version,
            m.manifest.module_type.value,
            "✓" if m.active else "✗",
            str(m.manifest.size_mb),
        )
    console.print(table)


@main.command()
@click.argument("query", required=False, default="")
def discover(query: str) -> None:
    """Search installed modules."""
    manager = _default_manager()
    results = manager.discover(query)
    if not results:
        console.print("[yellow]No modules found.[/yellow]")
        return
    table = Table(title="Module Search Results")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")
    for m in results:
        table.add_row(m.manifest.name, m.manifest.version, m.manifest.description[:80])
    console.print(table)


@main.command()
def status() -> None:
    """Show module composition and active state."""
    manager = _default_manager()
    composition = manager.compose()
    console.print_json(data=composition)


@main.command()
def doctor() -> None:
    """Verify module library integrity."""
    db = _default_db()
    modules = db.list_modules()
    missing = [m for m in modules if not m.path.exists()]
    console.print(f"Installed modules: {len(modules)}")
    console.print(f"Missing packages: {len(missing)}")
    if missing:
        for m in missing:
            console.print(f" - {m.manifest.name} {m.manifest.version} at {m.path}")


def main_entry() -> None:
    main()


if __name__ == "__main__":
    main_entry()
