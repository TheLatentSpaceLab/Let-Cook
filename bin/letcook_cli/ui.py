"""Rich-based status panel, post-loop menu, and interactive keypress handling."""

import os
import re
import select
import subprocess
import sys
import termios
import tty
from pathlib import Path
from typing import Optional

from rich import box
from rich.panel import Panel
from rich.table import Table

from .config import STATUS_STYLES, TOOL_DESCRIPTIONS, VERSION
from .console import console
from .loop_state import format_score_history, score_trend


def build_status_panel(
    goal: str,
    prog_type: str,
    tool_name: str,
    iteration: int,
    max_iter: int,
    threshold: int,
    score: str,
    status: str,
    elapsed: str,
    hard: int,
    soft: int,
    output_dir: str,
    allowed_tools: Optional[list[str]] = None,
    scores: Optional[list[int]] = None,
    eta: Optional[str] = None,
) -> Panel:
    """Build a rich Panel showing the current loop status."""
    style = STATUS_STYLES.get(status, "bold white")

    # Progress bar
    pct = iteration / max_iter if max_iter > 0 else 0
    bar_width = 20
    filled = int(pct * bar_width)
    bar = f"[green]{'━' * filled}[/green][dim]{'━' * (bar_width - filled)}[/dim]"

    # Score display with trend
    trend = score_trend(scores) if scores else ""
    if score != "-":
        score_num = int(score)
        if score_num >= threshold:
            score_display = f"[bold green]{score}[/bold green] / {threshold}{trend}"
        elif score_num >= threshold * 0.7:
            score_display = f"[bold yellow]{score}[/bold yellow] / {threshold}{trend}"
        else:
            score_display = f"[bold red]{score}[/bold red] / {threshold}{trend}"
    else:
        score_display = "[dim]—[/dim]"

    # Status with icon
    status_icons: dict[str, str] = {
        "ready":             "◯",
        "running":           "◉",
        "passed":            "✓",
        "completed":         "✓",
        "done":              "✓",
        "failed":            "✗",
        "exhausted":         "✗",
        "needs_improvement": "△",
        "stopped":           "⏹",
    }
    icon = status_icons.get(status, "?")

    # Truncate goal
    max_goal = 46
    display_goal = (goal[:max_goal - 1] + "…") if len(goal) > max_goal else goal

    # Build info table
    info = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    info.add_column("key", style="dim", width=14, no_wrap=True)
    info.add_column("value")

    info.add_row("Goal", f"[bold]{display_goal}[/bold]")
    info.add_row("Type", prog_type)
    info.add_row("Tool", tool_name)
    info.add_row("Iterations", f"{iteration} / {max_iter}  {bar}")
    info.add_row("Score", score_display)

    # Score history sparkline
    if scores and len(scores) > 1:
        info.add_row("History", format_score_history(scores))

    info.add_row("Constraints", f"{hard} hard · {soft} soft")
    info.add_row("Output", f"[dim]{output_dir}[/dim]")
    info.add_row("", "")
    info.add_row("Status", f"[{style}]{icon} {status}[/{style}]")

    # Elapsed + ETA
    elapsed_display = elapsed
    if eta and status == "running":
        elapsed_display += f"  [dim]ETA: ~{eta}[/dim]"
    info.add_row("Elapsed", elapsed_display)

    # Build allowed tools section for Claude
    if allowed_tools:
        info.add_row("", "")
        tools_table = Table(
            show_header=True, box=box.SIMPLE, padding=(0, 1),
            header_style="bold dim", expand=True,
        )
        tools_table.add_column("Allowed Tool", style="cyan", no_wrap=True)
        tools_table.add_column("Description", style="dim")
        for tool in allowed_tools:
            desc = TOOL_DESCRIPTIONS.get(tool, "")
            tools_table.add_row(tool, desc)
        info.add_row("Tools", tools_table)

    info.add_row("", "")
    info.add_row("Log", "[dim italic]tail -f .letcook.log[/dim italic]")
    info.add_row("", "[dim italic]Press ESC to stop gracefully[/dim italic]")

    return Panel(
        info,
        title="[bold]🍳 letcook[/bold]",
        subtitle=f"[dim]v{VERSION}[/dim]",
        border_style="bright_blue",
        padding=(1, 2),
        expand=False,
        width=64,
    )


# --- Post-loop interactive menu ---

def read_key_with_timeout(timeout: float = 0.0) -> Optional[str]:
    """Read a single keypress, optionally with timeout. Returns None on timeout."""
    stdin_fd = sys.stdin.fileno()
    old_settings = None
    try:
        old_settings = termios.tcgetattr(stdin_fd)
        tty.setcbreak(stdin_fd)
        if timeout > 0:
            ready, _, _ = select.select([stdin_fd], [], [], timeout)
            if not ready:
                return None
        ch = os.read(stdin_fd, 1)
        return ch.decode("utf-8", errors="ignore")
    except (termios.error, OSError):
        return None
    finally:
        if old_settings is not None:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)


def print_loop_summary(loop_state_file: Path) -> None:
    """Print the Summary section from loop-state.md."""
    if not loop_state_file.exists():
        console.print("[dim]No loop-state.md found.[/dim]")
        return

    lines = loop_state_file.read_text().splitlines()
    in_summary = False
    summary_lines: list[str] = []
    for line in lines:
        if re.match(r"^##\s+Summary", line):
            in_summary = True
            continue
        if in_summary:
            if re.match(r"^##\s", line):
                break
            summary_lines.append(line)

    if not summary_lines:
        console.print("[dim]No summary section found in loop-state.md.[/dim]")
        return

    console.print(Panel(
        "\n".join(summary_lines).strip(),
        title="[bold]Summary[/bold]",
        border_style="green",
        padding=(1, 2),
    ))


def show_git_diff() -> None:
    """Show git diff --stat for changes made during the run."""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=10,
        )
        if result.stdout.strip():
            console.print(Panel(
                result.stdout.strip(),
                title="[bold]Changes[/bold]",
                border_style="cyan",
                padding=(1, 2),
            ))
        else:
            console.print("[dim]No uncommitted changes detected.[/dim]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[dim]Could not run git diff.[/dim]")


def post_loop_menu(
    tool_label: str,
    goal: str,
    prog_type: str,
    max_iter: int,
    threshold: int,
    hard: int,
    soft: int,
    output_dir: str,
    allowed_tools: Optional[list[str]] = None,
) -> Optional[str]:
    """Show interactive post-loop menu. Returns 'continue' or None."""
    console.print()
    console.print(Panel(
        "  [bold cyan][s][/bold cyan] Show summary\n"
        "  [bold cyan][d][/bold cyan] Show diff\n"
        "  [bold cyan][c][/bold cyan] Continue with more iterations\n"
        "  [bold cyan][q][/bold cyan] Quit",
        title="[bold]What next?[/bold]",
        border_style="bright_blue",
        padding=(1, 2),
        width=44,
    ))

    while True:
        key = read_key_with_timeout(timeout=60.0)
        if key is None:
            return None
        if key == "q":
            return None
        if key == "s":
            console.print()
            print_loop_summary(Path("loop-state.md"))
            console.print("\n[dim]Press any key to return to menu, q to quit[/dim]")
            k = read_key_with_timeout(timeout=60.0)
            if k == "q":
                return None
            console.print()
            console.print(Panel(
                "  [bold cyan][s][/bold cyan] Show summary\n"
                "  [bold cyan][d][/bold cyan] Show diff\n"
                "  [bold cyan][c][/bold cyan] Continue with more iterations\n"
                "  [bold cyan][q][/bold cyan] Quit",
                title="[bold]What next?[/bold]",
                border_style="bright_blue",
                padding=(1, 2),
                width=44,
            ))
        elif key == "d":
            console.print()
            show_git_diff()
            console.print("\n[dim]Press any key to return to menu, q to quit[/dim]")
            k = read_key_with_timeout(timeout=60.0)
            if k == "q":
                return None
            console.print()
            console.print(Panel(
                "  [bold cyan][s][/bold cyan] Show summary\n"
                "  [bold cyan][d][/bold cyan] Show diff\n"
                "  [bold cyan][c][/bold cyan] Continue with more iterations\n"
                "  [bold cyan][q][/bold cyan] Quit",
                title="[bold]What next?[/bold]",
                border_style="bright_blue",
                padding=(1, 2),
                width=44,
            ))
        elif key == "c":
            return "continue"
