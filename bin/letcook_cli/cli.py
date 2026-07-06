"""Argument parsing and command dispatch."""

import sys

from .commands import cmd_continue, cmd_help, cmd_run, cmd_version
from .console import console
from .scaffold import cmd_init, cmd_validate


def main() -> None:
    """Entry point."""
    args = sys.argv[1:]
    cmd = args[0] if args else "help"
    rest = args[1:]

    commands: dict[str, object] = {
        "init": lambda: cmd_init(rest),
        "run": lambda: cmd_run(rest),
        "continue": lambda: cmd_continue(rest),
        "validate": lambda: cmd_validate(rest),
        "help": cmd_help,
        "version": cmd_version,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        console.print(f"[bold red]Unknown command: {cmd}[/bold red]")
        console.print()
        cmd_help()
        sys.exit(1)
