"""Parsing helpers for the markdown spec files (PROGRAM.md, RESTRICTIONS.md)."""

import re
from pathlib import Path


def parse_frontmatter(file: Path) -> dict[str, str]:
    """Extract YAML-like frontmatter fields from a markdown file."""
    text = file.read_text()
    match = re.match(r"^---\n(.*?\n)---", text, re.DOTALL)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^(\w+):\s*(.+?)(?:\s*#.*)?$", line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def parse_goal(file: Path) -> str:
    """Extract the first non-empty line from the ## Goal section."""
    in_goal = False
    for line in file.read_text().splitlines():
        if re.match(r"^##\s+Goal", line):
            in_goal = True
            continue
        if in_goal:
            if re.match(r"^##\s", line):
                break
            if line.startswith("<!--") or not line.strip():
                continue
            return line.strip()
    return "(not set)"


def count_constraints(file: Path, section: str) -> int:
    """Count bullet items in a named section."""
    in_section = False
    count = 0
    for line in file.read_text().splitlines():
        if re.match(rf'^##\s+{re.escape(section)}', line):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", line):
                break
            if line.startswith("<!--"):
                continue
            if re.match(r"^-\s+\S", line):
                count += 1
    return count


def section_has_content(file: Path, section: str) -> bool:
    """Check if a markdown section has non-comment, non-empty content."""
    in_section = False
    for line in file.read_text().splitlines():
        if re.match(rf'^##\s+{re.escape(section)}', line):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", line):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False
