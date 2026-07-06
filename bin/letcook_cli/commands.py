"""Top-level CLI commands: help, version, run, and continue."""

import os
import shutil
import sys
from pathlib import Path

from rich import box
from rich.panel import Panel
from rich.table import Table

from .config import CLAUDE_BASE_TOOLS, CLAUDE_TOOLS_BY_TYPE, KNOWN_TOOLS, VERSION
from .console import console
from .loop_state import parse_loop_state
from .runner import run_monitored_loop
from .specs import count_constraints, parse_frontmatter, parse_goal
from .ui import post_loop_menu


def cmd_help() -> None:
    """Show help message."""
    help_table = Table(
        show_header=True, box=box.ROUNDED, border_style="bright_blue",
        title="[bold]🍳 letcook[/bold] — let them cook",
        padding=(0, 1),
    )
    help_table.add_column("Command", style="bold cyan", no_wrap=True)
    help_table.add_column("Description")

    help_table.add_row("init [dir] [--type TYPE]", "Scaffold a new project")
    help_table.add_row("run  [dir] [tool]", "Run the loop with a specific tool")
    help_table.add_row("continue [dir] [tool]", "Resume a previous run")
    help_table.add_row("validate [dir]", "Check project files before running")
    help_table.add_row("help", "Show this help")
    help_table.add_row("version", "Show version")

    console.print()
    console.print(help_table)
    console.print()

    tools_table = Table(
        show_header=True, box=box.SIMPLE, padding=(0, 1),
        title="[bold]Supported Tools[/bold]",
    )
    tools_table.add_column("Tool", style="cyan", no_wrap=True)
    tools_table.add_column("Description", style="dim")

    tools = [
        ("claude", "Claude Code (headless CLI)"),
        ("qubito", "Qubito (headless CLI)"),
        ("cursor", "Cursor (rules file)"),
        ("windsurf", "Windsurf (rules file)"),
        ("continue", "Continue.dev (rules file)"),
        ("aider", "Aider (config file)"),
        ("codex", "OpenAI Codex CLI"),
        ("copilot", "GitHub Copilot CLI"),
    ]
    for name, desc in tools:
        tools_table.add_row(name, desc)

    console.print(tools_table)
    console.print()

    types_table = Table(
        show_header=True, box=box.SIMPLE, padding=(0, 1),
        title="[bold]Project Types[/bold] (for init --type)",
    )
    types_table.add_column("Type", style="cyan", no_wrap=True)
    types_table.add_column("Description", style="dim")

    types = [
        ("build", "Write code, run tests (default)"),
        ("research", "Read sources, synthesize findings"),
        ("content", "Write articles, scripts, media"),
        ("experiment", "Run experiments, log metrics"),
        ("refactor", "Restructure existing code"),
    ]
    for name, desc in types:
        types_table.add_row(name, desc)

    console.print(types_table)
    console.print()

    console.print("[dim]Examples:[/dim]")
    console.print("  letcook init                            [dim]# scaffold in current dir[/dim]")
    console.print("  letcook init ./my-task                  [dim]# scaffold in a subdirectory[/dim]")
    console.print("  letcook init ./my-task --type research  [dim]# scaffold with research templates[/dim]")
    console.print("  letcook run  claude                     [dim]# run in current dir with Claude[/dim]")
    console.print("  letcook run  ./my-task claude           [dim]# run a specific task[/dim]")
    console.print("  letcook continue ./my-task claude       [dim]# resume a previous run[/dim]")
    console.print("  letcook validate ./my-task              [dim]# check project before running[/dim]")
    console.print()


def cmd_version() -> None:
    """Print version."""
    console.print(f"[bold]letcook[/bold] {VERSION}")


def get_allowed_tools(prog_type: str, extra_tools: str = "") -> list[str]:
    """Get the full allowed tools list for a program type + extras."""
    tools = CLAUDE_BASE_TOOLS + CLAUDE_TOOLS_BY_TYPE.get(prog_type, [])
    if extra_tools:
        for t in extra_tools.split(","):
            t = t.strip()
            if t and t not in tools:
                tools.append(t)
    return tools


def _parse_run_args(args: list[str]) -> tuple[Path, str]:
    """Parse [dir] and [tool] from run/continue args."""
    target_dir = Path(".")
    tool = ""
    i = 0
    while i < len(args):
        if args[i] == "--tool" and i + 1 < len(args):
            tool = args[i + 1]
            i += 2
        elif args[i] in KNOWN_TOOLS:
            tool = args[i]
            i += 1
        else:
            target_dir = Path(args[i])
            i += 1
    return target_dir, tool


def _load_project_metadata(target_dir: Path) -> dict:
    """Load and parse project metadata from specs files."""
    program_file = target_dir / "specs" / "PROGRAM.md"
    restrictions_file = target_dir / "specs" / "RESTRICTIONS.md"

    fm = parse_frontmatter(program_file)
    return {
        "prog_type": fm.get("type", "build"),
        "max_iter": int(fm.get("iterations", "5")),
        "threshold": int(fm.get("completion_threshold", "90")),
        "output_dir": fm.get("output", "./output/"),
        "extra_tools": fm.get("tools", ""),
        "goal": parse_goal(program_file),
        "hard": count_constraints(restrictions_file, "Hard Constraints"),
        "soft": count_constraints(restrictions_file, "Soft Constraints"),
    }


def _run_with_tool(
    tool: str,
    detected: str,
    target_dir: Path,
    prompt: str,
    meta: dict,
    is_continue: bool = False,
) -> None:
    """Dispatch to the appropriate tool runner."""
    if tool == "claude":
        allowed_tools = get_allowed_tools(meta["prog_type"], meta["extra_tools"])
        allowed_tools_str = ",".join(allowed_tools)
        tool_label = f"claude{detected}"

        os.chdir(target_dir)

        exit_code, stopped = run_monitored_loop(
            cmd=["claude", "-p", prompt, "--allowedTools", allowed_tools_str],
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
            allowed_tools=allowed_tools,
        )

        # Post-loop menu
        action = post_loop_menu(
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
            allowed_tools=allowed_tools,
        )
        if action == "continue" and not is_continue:
            _do_continue_loop(tool, detected, meta)

        sys.exit(exit_code)

    elif tool == "qubito":
        tool_label = f"qubito{detected}"

        os.chdir(target_dir)

        exit_code, stopped = run_monitored_loop(
            cmd=["qubito", "-p", prompt],
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
        )

        action = post_loop_menu(
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
        )
        if action == "continue" and not is_continue:
            _do_continue_loop(tool, detected, meta)

        sys.exit(exit_code)

    elif tool == "aider":
        console.print(f"[bold cyan]Running with Aider{detected}…[/bold cyan]")
        console.print()
        os.execvp("aider", [
            "aider",
            "--read", str(target_dir / "specs" / "SKILL.md"),
            "--read", str(target_dir / "specs" / "PROGRAM.md"),
            "--read", str(target_dir / "specs" / "RESTRICTIONS.md"),
            "--message", prompt,
        ])

    elif tool == "codex":
        console.print(f"[bold cyan]Running with Codex CLI{detected}…[/bold cyan]")
        console.print()
        os.chdir(target_dir)
        os.execvp("codex", ["codex", "exec", prompt])

    elif tool == "copilot":
        console.print(
            f"[bold cyan]Running with GitHub Copilot CLI{detected}…[/bold cyan]"
        )
        console.print()
        os.chdir(target_dir)
        os.execvp("copilot", ["copilot", "-p", prompt])

    elif not tool:
        console.print(
            Panel(
                "[bold yellow]No AI tool detected.[/bold yellow]\n\n"
                "Paste this prompt into your AI assistant:\n\n"
                f"  [bold]{prompt}[/bold]\n\n"
                "[dim]Or install one of: claude, qubito, aider, codex, copilot[/dim]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    else:
        console.print(
            Panel(
                f"[bold yellow]Tool '{tool}' doesn't support headless execution."
                "[/bold yellow]\n\n"
                f"Open the project in your IDE and tell the AI:\n\n"
                "  [bold]Start working on this project.[/bold]",
                border_style="yellow",
                padding=(1, 2),
            )
        )


def _do_continue_loop(tool: str, detected: str, meta: dict) -> None:
    """Run a continue loop from within the post-loop menu."""
    loop_state_file = Path("loop-state.md")
    iteration, score, status = parse_loop_state(loop_state_file)

    continue_prompt = (
        f"Read specs/SKILL.md, specs/PROGRAM.md, specs/RESTRICTIONS.md, and loop-state.md. "
        f"The previous run ended at iteration {iteration} with score {score}. "
        f"Continue the autonomous loop for up to {meta['max_iter']} more iterations. "
        f"Resume from the current state and address the evaluator's feedback."
    )

    if tool == "claude":
        allowed_tools = get_allowed_tools(meta["prog_type"], meta["extra_tools"])
        allowed_tools_str = ",".join(allowed_tools)
        tool_label = f"claude{detected}"

        exit_code, _ = run_monitored_loop(
            cmd=["claude", "-p", continue_prompt, "--allowedTools", allowed_tools_str],
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
            allowed_tools=allowed_tools,
        )
    elif tool == "qubito":
        tool_label = f"qubito{detected}"
        exit_code, _ = run_monitored_loop(
            cmd=["qubito", "-p", continue_prompt],
            tool_label=tool_label,
            goal=meta["goal"],
            prog_type=meta["prog_type"],
            max_iter=meta["max_iter"],
            threshold=meta["threshold"],
            hard=meta["hard"],
            soft=meta["soft"],
            output_dir=meta["output_dir"],
        )


def cmd_run(args: list[str]) -> None:
    """Run the autonomous loop."""
    target_dir, tool = _parse_run_args(args)

    # Validate project files
    for spec in ["specs/SKILL.md", "specs/PROGRAM.md", "specs/RESTRICTIONS.md"]:
        if not (target_dir / spec).exists():
            console.print(f"[bold red]Missing {target_dir / spec}[/bold red]")
            console.print(f"Run [cyan]letcook init {target_dir}[/cyan] first.")
            sys.exit(1)

    prompt = (
        "Read specs/SKILL.md, specs/PROGRAM.md, and specs/RESTRICTIONS.md, "
        "then execute the autonomous loop as defined in specs/SKILL.md."
    )

    # Auto-detect tool
    detected = ""
    if not tool:
        for candidate in ["claude", "qubito", "aider", "codex", "copilot"]:
            if shutil.which(candidate):
                tool = candidate
                detected = " (auto-detected)"
                break

    meta = _load_project_metadata(target_dir)

    console.print()
    _run_with_tool(tool, detected, target_dir, prompt, meta)


def cmd_continue(args: list[str]) -> None:
    """Continue a previous run from where it left off."""
    target_dir, tool = _parse_run_args(args)

    # Validate project files
    for spec in ["specs/SKILL.md", "specs/PROGRAM.md", "specs/RESTRICTIONS.md"]:
        if not (target_dir / spec).exists():
            console.print(f"[bold red]Missing {target_dir / spec}[/bold red]")
            console.print(f"Run [cyan]letcook init {target_dir}[/cyan] first.")
            sys.exit(1)

    loop_state_file = target_dir / "loop-state.md"
    if not loop_state_file.exists():
        console.print("[bold red]No loop-state.md found.[/bold red]")
        console.print("Run [cyan]letcook run[/cyan] first to start a loop.")
        sys.exit(1)

    iteration, score, status = parse_loop_state(loop_state_file)
    meta = _load_project_metadata(target_dir)

    console.print()
    console.print(
        Panel(
            f"[bold]Continuing from iteration {iteration} "
            f"(score: {score})…[/bold]",
            border_style="bright_blue",
            padding=(0, 1),
        )
    )

    prompt = (
        f"Read specs/SKILL.md, specs/PROGRAM.md, specs/RESTRICTIONS.md, and loop-state.md. "
        f"The previous run ended at iteration {iteration} with score {score}. "
        f"Continue the autonomous loop for up to {meta['max_iter']} more iterations. "
        f"Resume from the current state and address the evaluator's feedback."
    )

    # Auto-detect tool
    detected = ""
    if not tool:
        for candidate in ["claude", "qubito", "aider", "codex", "copilot"]:
            if shutil.which(candidate):
                tool = candidate
                detected = " (auto-detected)"
                break

    _run_with_tool(tool, detected, target_dir, prompt, meta, is_continue=True)
