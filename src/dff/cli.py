from __future__ import annotations

import typer

from dff import __version__

app = typer.Typer(
    name="dff",
    help="Terminal UI diff viewer for jujutsu and git.",
    no_args_is_help=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(f"dff {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        typer.echo("dff: TUI not yet implemented. See README.md for the roadmap.")
        raise typer.Exit(0)
