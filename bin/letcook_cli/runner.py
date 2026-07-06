"""Monitored execution of the headless AI tool loop."""

import os
import select
import signal
import subprocess
import sys
import termios
import time
import tty
from pathlib import Path
from typing import Optional

from .console import console
from .loop_state import format_elapsed, parse_loop_state, parse_score_history
from .ui import build_status_panel


def run_monitored_loop(
    cmd: list[str],
    tool_label: str,
    goal: str,
    prog_type: str,
    max_iter: int,
    threshold: int,
    hard: int,
    soft: int,
    output_dir: str,
    allowed_tools: Optional[list[str]] = None,
) -> tuple[int, bool]:
    """Run a headless AI tool with live monitoring.

    Returns (exit_code, stopped_by_user).
    """
    start_time = int(time.time())
    log_file = Path(".letcook.log")
    stopped_by_user = False
    prev_iteration = 0
    iteration_start_time = start_time
    iteration_durations: list[float] = []

    with open(log_file, "w") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)

        old_settings = None
        stdin_fd = sys.stdin.fileno()
        try:
            old_settings = termios.tcgetattr(stdin_fd)
            tty.setcbreak(stdin_fd)
        except (termios.error, OSError):
            pass

        try:
            while proc.poll() is None:
                loop_state_file = Path("loop-state.md")
                iteration, score, status = parse_loop_state(loop_state_file)
                scores = parse_score_history(loop_state_file)

                # Track iteration durations for ETA
                now = int(time.time())
                if iteration > prev_iteration:
                    if prev_iteration > 0:
                        duration = now - iteration_start_time
                        iteration_durations.append(duration)
                    iteration_start_time = now
                    prev_iteration = iteration

                # Calculate ETA
                eta = None
                if iteration > 0 and iteration_durations:
                    avg_dur = sum(iteration_durations) / len(iteration_durations)
                    remaining = max_iter - iteration
                    if remaining > 0:
                        eta = format_elapsed(int(avg_dur * remaining))

                if proc.poll() is None:
                    status = status if status != "ready" else "running"
                elapsed = format_elapsed(now - start_time)

                console.clear()
                console.print(build_status_panel(
                    goal, prog_type, tool_label, iteration, max_iter,
                    threshold, score, status, elapsed, hard, soft,
                    output_dir, allowed_tools=allowed_tools,
                    scores=scores, eta=eta,
                ))

                if old_settings is not None:
                    ready, _, _ = select.select([stdin_fd], [], [], 3)
                    if ready:
                        ch = os.read(stdin_fd, 1)
                        if ch == b'\x1b':
                            stopped_by_user = True
                            proc.send_signal(signal.SIGTERM)
                            proc.wait(timeout=10)
                            break
                else:
                    time.sleep(3)
        except KeyboardInterrupt:
            stopped_by_user = True
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=10)
        finally:
            if old_settings is not None:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)

        exit_code = proc.returncode or 0

    # Final status display
    loop_state_file = Path("loop-state.md")
    iteration, score, status = parse_loop_state(loop_state_file)
    scores = parse_score_history(loop_state_file)
    if stopped_by_user:
        status = "stopped"
    elapsed = format_elapsed(int(time.time()) - start_time)

    console.clear()
    console.print(build_status_panel(
        goal, prog_type, tool_label, iteration, max_iter, threshold,
        score, status, elapsed, hard, soft, output_dir,
        allowed_tools=allowed_tools, scores=scores,
    ))
    console.print()

    if stopped_by_user:
        console.print("[bold yellow]⏹ Stopped by user.[/bold yellow]")
    elif exit_code == 0:
        console.print("[bold green]✓ Done.[/bold green]")
    else:
        console.print(f"[bold red]✗ Tool exited with code {exit_code}[/bold red]")

    return exit_code, stopped_by_user
