"""Parsing and formatting helpers for loop-state.md."""

import re
from pathlib import Path


def parse_loop_state(file: Path) -> tuple[int, str, str]:
    """Parse loop-state.md and return (iteration, score, status)."""
    if not file.exists():
        return (0, "-", "ready")
    iteration, score, status = 0, "-", "ready"
    for line in file.read_text().splitlines():
        m = re.match(r"^##\s+Iteration\s+(\d+)", line)
        if m:
            iteration = int(m.group(1))
        m = re.match(r"^\*\*Score\*\*:\s*(\d+)", line)
        if m:
            score = m.group(1)
        m = re.match(r"^\*\*Status\*\*:\s*(.+)", line)
        if m:
            status = m.group(1).strip()
        if re.match(r"^##\s+Summary", line):
            status = "done"
    return (iteration, score, status)


def parse_score_history(file: Path) -> list[int]:
    """Extract all iteration scores from loop-state.md in order."""
    if not file.exists():
        return []
    scores: list[int] = []
    for line in file.read_text().splitlines():
        m = re.match(r"^\*\*Score\*\*:\s*(\d+)", line)
        if m:
            scores.append(int(m.group(1)))
    return scores


def score_trend(scores: list[int]) -> str:
    """Return a rich-formatted trend indicator from score history."""
    if len(scores) < 2:
        return ""
    diff = scores[-1] - scores[-2]
    if diff > 0:
        return f" [green]↑+{diff}[/green]"
    elif diff < 0:
        return f" [red]↓{diff}[/red]"
    return " [dim]→[/dim]"


def format_elapsed(seconds: int) -> str:
    """Format seconds as human-readable elapsed time."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def format_score_history(scores: list[int]) -> str:
    """Format score history as a compact sparkline-style display."""
    if not scores:
        return ""
    parts: list[str] = []
    for s in scores:
        if s >= 90:
            parts.append(f"[green]{s}[/green]")
        elif s >= 60:
            parts.append(f"[yellow]{s}[/yellow]")
        else:
            parts.append(f"[red]{s}[/red]")
    return " → ".join(parts)
