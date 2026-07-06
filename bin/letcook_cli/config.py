"""Constants and install-path resolution shared across letcook."""

import os
from pathlib import Path

VERSION = "0.3.0"

# --- Resolve install directory ---
# This file lives at <LETCOOK_HOME>/bin/letcook_cli/config.py
SCRIPT_PATH = Path(os.path.realpath(__file__)).parent.parent
LETCOOK_HOME = SCRIPT_PATH.parent

# --- Tool config ---

CLAUDE_BASE_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent"]

CLAUDE_TOOLS_BY_TYPE: dict[str, list[str]] = {
    "build":      [],
    "refactor":   [],
    "research":   ["WebSearch", "WebFetch"],
    "content":    ["WebSearch", "WebFetch"],
    "experiment": ["WebSearch", "WebFetch", "NotebookEdit"],
}

TOOL_DESCRIPTIONS: dict[str, str] = {
    "Read":         "Read files",
    "Write":        "Create/overwrite files",
    "Edit":         "Targeted file edits",
    "Bash":         "Run shell commands",
    "Glob":         "Find files by pattern",
    "Grep":         "Search file contents",
    "Agent":        "Spawn subagents",
    "WebSearch":    "Web search",
    "WebFetch":     "Fetch URL content",
    "NotebookEdit": "Edit Jupyter notebooks",
}

VALID_TYPES = {"build", "research", "content", "experiment", "refactor"}

KNOWN_TOOLS = {"claude", "qubito", "cursor", "windsurf", "continue", "aider", "codex", "copilot"}

STATUS_STYLES: dict[str, str] = {
    "ready":             "bold cyan",
    "running":           "bold yellow",
    "passed":            "bold green",
    "completed":         "bold green",
    "done":              "bold green",
    "failed":            "bold red",
    "exhausted":         "bold red",
    "needs_improvement": "bold yellow",
    "stopped":           "bold yellow",
}
