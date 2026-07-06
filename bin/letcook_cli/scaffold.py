"""Project scaffolding: file copying, tool integrations, and validation."""

import shutil
import sys
from pathlib import Path

from rich.panel import Panel

from .config import LETCOOK_HOME, VALID_TYPES
from .console import console
from .specs import count_constraints, parse_frontmatter, parse_goal, section_has_content


def copy_if_missing(src: Path, dst: Path) -> None:
    """Copy a file if it doesn't already exist at the destination."""
    if dst.exists():
        console.print(f"  [yellow]SKIP[/yellow]   {dst} [dim](already exists)[/dim]")
    else:
        shutil.copy2(src, dst)
        console.print(f"  [green]CREATE[/green] {dst}")


# --- Tool integration installer ---

def install_tool_integration(tool: str, target: Path) -> None:
    """Install tool-specific integration files into the target directory."""
    integrations: dict[str, list[tuple[str, str]]] = {
        "claude": [
            ("integrations/claude/skills/start-project/SKILL.md",
             ".claude/skills/start-project/SKILL.md"),
            ("integrations/claude/skills/start-working/SKILL.md",
             ".claude/skills/start-working/SKILL.md"),
        ],
        "cursor": [
            ("integrations/cursor/autonomous-loop.mdc",
             ".cursor/rules/autonomous-loop.mdc"),
        ],
        "windsurf": [
            ("integrations/windsurf/autonomous-loop.md",
             ".windsurf/rules/autonomous-loop.md"),
        ],
        "continue": [
            ("integrations/continue/autonomous-loop.md",
             ".continue/rules/autonomous-loop.md"),
        ],
        "aider": [
            ("integrations/aider/.aider.conf.yml", ".aider.conf.yml"),
        ],
    }

    if tool not in integrations:
        console.print(
            f"  [yellow]Unknown tool '{tool}'. "
            f"Supported: {', '.join(integrations)}[/yellow]"
        )
        return

    for src_rel, dst_rel in integrations[tool]:
        src = LETCOOK_HOME / src_rel
        dst = target / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy_if_missing(src, dst)


# --- Validation ---

def validate_project(target_dir: Path) -> tuple[list[str], list[str]]:
    """Validate project files. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # Check required files exist
    for spec in ["specs/SKILL.md", "specs/PROGRAM.md", "specs/RESTRICTIONS.md"]:
        if not (target_dir / spec).exists():
            errors.append(f"Missing {spec}")

    if errors:
        return errors, warnings

    program_file = target_dir / "specs" / "PROGRAM.md"
    restrictions_file = target_dir / "specs" / "RESTRICTIONS.md"

    # Validate frontmatter
    fm = parse_frontmatter(program_file)
    if not fm:
        errors.append("No YAML frontmatter found in specs/PROGRAM.md")
    else:
        prog_type = fm.get("type", "")
        if prog_type and prog_type not in VALID_TYPES:
            errors.append(
                f"Invalid type '{prog_type}' — "
                f"must be one of: {', '.join(sorted(VALID_TYPES))}"
            )

        iterations = fm.get("iterations", "5")
        if not iterations.isdigit() or int(iterations) < 1:
            errors.append(f"Invalid iterations '{iterations}' — must be a positive integer")

        threshold = fm.get("completion_threshold", "90")
        if not threshold.isdigit() or not (0 <= int(threshold) <= 100):
            errors.append(f"Invalid completion_threshold '{threshold}' — must be 0-100")

    # Validate goal
    goal = parse_goal(program_file)
    if goal == "(not set)":
        errors.append("No goal defined — fill in the ## Goal section in specs/PROGRAM.md")

    # Validate success criteria
    if not section_has_content(restrictions_file, "Success Criteria"):
        errors.append("No success criteria — add items to ## Success Criteria in specs/RESTRICTIONS.md")

    # Check for hard constraints in restrictions
    hard = count_constraints(restrictions_file, "Hard Constraints")
    if hard == 0:
        warnings.append("No hard constraints in specs/RESTRICTIONS.md — the evaluator has nothing to enforce")

    # Check soft constraints
    soft = count_constraints(restrictions_file, "Soft Constraints")
    if soft == 0:
        warnings.append("No soft constraints in specs/RESTRICTIONS.md")

    # Check context section
    if not section_has_content(program_file, "Context"):
        warnings.append("Empty ## Context section — consider adding background for the producer")

    return errors, warnings


# --- Commands ---

def cmd_init(args: list[str]) -> None:
    """Scaffold a new project, optionally with type-specific templates."""
    target_dir = Path(".")
    proj_type = "build"

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            proj_type = args[i + 1]
            i += 2
        else:
            target_dir = Path(args[i])
            i += 1

    if proj_type not in VALID_TYPES:
        console.print(
            f"[bold red]Invalid type '{proj_type}'[/bold red] — "
            f"must be one of: {', '.join(sorted(VALID_TYPES))}"
        )
        sys.exit(1)

    specs_dir = target_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(
        Panel(
            f"[bold]Initializing [cyan]{proj_type}[/cyan] project…[/bold]",
            border_style="bright_blue",
            padding=(0, 1),
        )
    )
    console.print()

    copy_if_missing(LETCOOK_HOME / "SKILL.md", specs_dir / "SKILL.md")

    # Use type-specific templates if available, otherwise fall back to generic
    type_template_dir = LETCOOK_HOME / "templates" / proj_type
    if type_template_dir.exists():
        copy_if_missing(type_template_dir / "PROGRAM.md", specs_dir / "PROGRAM.md")
        copy_if_missing(
            type_template_dir / "RESTRICTIONS.md", specs_dir / "RESTRICTIONS.md"
        )
    else:
        copy_if_missing(
            LETCOOK_HOME / "templates" / "PROGRAM.md", specs_dir / "PROGRAM.md"
        )
        copy_if_missing(
            LETCOOK_HOME / "templates" / "RESTRICTIONS.md",
            specs_dir / "RESTRICTIONS.md",
        )

    console.print()
    console.print("[bold green]Project initialized![/bold green]")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print(f"  1. Edit [bold]{specs_dir}/PROGRAM.md[/bold]      — define your task")
    console.print(f"  2. Edit [bold]{specs_dir}/RESTRICTIONS.md[/bold] — set quality gates")
    console.print(f"  3. Validate: [cyan]letcook validate {target_dir}[/cyan]")
    console.print(f"  4. Run:      [cyan]letcook run {target_dir}[/cyan]")
    console.print()


def cmd_validate(args: list[str]) -> None:
    """Validate project files before running."""
    target_dir = Path(args[0]) if args else Path(".")

    console.print()
    console.print(
        Panel(
            f"[bold]Validating project in [cyan]{target_dir}[/cyan]…[/bold]",
            border_style="bright_blue",
            padding=(0, 1),
        )
    )
    console.print()

    errors, warnings = validate_project(target_dir)

    if errors:
        for err in errors:
            console.print(f"  [bold red]✗[/bold red] {err}")
    if warnings:
        for warn in warnings:
            console.print(f"  [yellow]△[/yellow] {warn}")

    if not errors and not warnings:
        console.print("  [bold green]✓[/bold green] All checks passed")

    console.print()

    if errors:
        console.print(
            f"[bold red]Found {len(errors)} error(s).[/bold red] "
            "Fix them before running."
        )
        sys.exit(1)
    elif warnings:
        console.print(
            f"[yellow]{len(warnings)} warning(s)[/yellow] — "
            "consider addressing these for better results."
        )
    else:
        console.print("[bold green]Ready to run![/bold green]")
    console.print()
