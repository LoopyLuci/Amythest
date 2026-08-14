"""Tests for CLI entrypoint and module create/install workflow."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from amythest.cli.main import main
from amythest.types import ModuleType


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "install" in result.output


def test_cli_version(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_cli_create_module(tmp_path: Path, runner: CliRunner) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("python asyncio tasks", encoding="utf-8")
    dest = tmp_path / "out-module.apkg"
    result = runner.invoke(
        main,
        [
            "create",
            str(source),
            "--name",
            "notes",
            "--version",
            "1.0.0",
            "--author",
            "test",
            "--description",
            "Notes module",
            "--type",
            ModuleType.KNOWLEDGE.value,
            "--base-model",
            "amythest-base",
            "--base-model-version",
            "0.1.0",
            "--base-model-architecture",
            "dense-70b",
            "--output",
            str(dest),
        ],
    )
    assert result.exit_code == 0, result.output
    assert dest.exists()


def test_cli_create_missing_source(runner: CliRunner) -> None:
    result = runner.invoke(main, ["create", "/missing/path", "--name", "x", "--version", "1.0.0"])
    assert result.exit_code != 0
