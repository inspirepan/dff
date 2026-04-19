from __future__ import annotations

from typer.testing import CliRunner

from dff import __version__
from dff.cli import app


def test_version_flag_prints_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_no_args_exits_zero_with_placeholder_message() -> None:
    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    assert "TUI not yet implemented" in result.stdout
