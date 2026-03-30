# letcook

*Let them cook.* A **tool-agnostic** CLI for running autonomous producer/evaluator loops with AI coding assistants. Scaffold a project, define a task, set quality gates, and let the AI cook until it's done.

Works with **Claude Code**, **Cursor**, **Windsurf**, **Aider**, **Continue.dev**, **Codex CLI**, **GitHub Copilot**, or any AI tool that can read markdown files.

## Why

AI coding assistants are capable of much more than single-turn Q&A. Given a clear goal, success criteria, and quality constraints, they can autonomously execute multi-step tasks — writing code, evaluating their own output, and iterating on feedback — across dozens of cycles without human intervention.

The bottleneck is no longer the AI's ability. It's the **structure of the prompt**. A well-defined task with explicit acceptance criteria and a feedback loop produces dramatically better results than a vague instruction. This project provides that structure as a portable, reusable standard.

Inspired by Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch), which demonstrated that AI agents can autonomously run LLM training experiments overnight — modifying code, running 5-minute training runs, evaluating loss, and deciding whether to keep or discard changes — all while the human sleeps. **letcook** generalizes that pattern beyond ML experiments to any task type: building applications, conducting research, writing content, or refactoring code.

## Install

**One-liner:**

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/letcook/main/install.sh | bash
```

**From source:**

```bash
git clone <repo-url> ~/letcook
cd ~/letcook
make install
```

**For development** (symlink instead of copy):

```bash
git clone <repo-url> ~/letcook
cd ~/letcook
make link
```

Installs to `~/.letcook/` and symlinks `letcook` to `~/.local/bin/`. Make sure `~/.local/bin` is in your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Uninstall:**

```bash
make uninstall
# or just: rm -rf ~/.letcook ~/.local/bin/letcook
```

## Quick Start

```bash
# 1. Scaffold a new project
letcook init ./my-task

# 2. Edit the files
vim ./my-task/program.md         # define your task
vim ./my-task/restrictions.md    # set quality gates

# 3. Let him cook
letcook run ./my-task
```

That's it. `letcook run` auto-detects which AI tool is installed (Claude Code, Aider, Codex, Copilot) and runs it. If none is found, it prints the universal prompt to paste manually.

## CLI Reference

```
letcook init [dir] [--tool <tool>]   Scaffold a new project
letcook run  [dir] [--tool <tool>]   Run the loop with a specific tool
letcook help                         Show help
letcook version                      Show version
```

### `letcook init`

Creates `program.md`, `restrictions.md`, and `skill.md` in the target directory:

```bash
letcook init ./my-task                  # core files only
letcook init ./my-task --tool claude    # + Claude Code skills
letcook init ./my-task --tool cursor    # + Cursor rules
letcook init ./my-task --tool windsurf  # + Windsurf rules
letcook init ./my-task --tool aider     # + Aider config
letcook init ./my-task --tool continue  # + Continue.dev rules
```

Output:

```
my-task/
├── program.md        <- Define your task here
├── restrictions.md   <- Set quality gates here
└── skill.md          <- Execution engine (don't edit)
```

### `letcook run`

Runs the autonomous loop. Auto-detects your AI tool or specify one:

```bash
letcook run ./my-task                # auto-detect
letcook run ./my-task --tool claude  # force Claude Code
letcook run ./my-task --tool aider   # force Aider
letcook run ./my-task --tool codex   # force Codex CLI
```

What happens per tool:

| Tool | What `letcook run` does |
|------|------------------------|
| `claude` | Runs `claude -p` with pre-approved tools |
| `aider` | Runs `aider --read` with all project files |
| `codex` | Runs `codex exec` with the prompt |
| `copilot` | Runs `copilot -p` with the prompt |
| (none) | Prints the universal prompt to paste manually |
| `cursor` / `windsurf` / `continue` | Tells you to open the IDE and say "Start working" |

## Defining a Task

### program.md

The task definition. YAML frontmatter for config, markdown for instructions:

```markdown
---
type: build                  # build | research | content | experiment | refactor
iterations: 5                # max loop iterations
completion_threshold: 90     # score (0-100) to stop early
output: ./output/            # where artifacts are written
scope:                       # files/dirs the producer can touch
  - ./output/
---

## Goal

Build a Python CLI that converts markdown to HTML with syntax highlighting.

## Context

Use only stdlib + pygments. Target Python 3.10+.

## Success Criteria

- [ ] (hard) Accepts a file path argument or reads from stdin
- [ ] (hard) Produces valid HTML5 output
- [ ] (soft) Handles tables, lists, blockquotes
- [ ] (soft) Includes a --theme flag

## Notes

Keep it to a single file.
```

### restrictions.md

Quality gates the evaluator checks every iteration:

```markdown
# Restrictions

## Hard Constraints        <- must ALL pass or the iteration fails

- Type hints on all functions
- Functions under 30 lines
- Runs without errors

## Soft Constraints        <- scored, more passing = higher score

- Has docstrings on public functions
- Handles malformed input gracefully

## Out of Scope            <- things the producer must NEVER do

- Do not modify files outside the declared scope
- Do not add a web server
```

### Configuration

| Field | Default | Description |
|-------|---------|-------------|
| `type` | `build` | `build`, `research`, `content`, `experiment`, `refactor` |
| `iterations` | `5` | Maximum loop iterations |
| `completion_threshold` | `90` | Score (0-100) to stop early |
| `output` | `./output/` | Where artifacts are written |
| `scope` | `[./output/]` | Files/dirs the producer may touch |

### Task Types

| Type | Producer action | Evaluator checks |
|------|----------------|-----------------|
| `build` | Writes code, runs tests | Tests pass, restrictions met, runs cleanly |
| `research` | Reads sources, synthesizes findings | Accuracy, coverage, citations present |
| `content` | Writes articles, scripts, media | Tone, structure, accuracy, audience fit |
| `experiment` | Runs experiments, logs metrics | Metrics improving, valid methodology |
| `refactor` | Restructures existing code | Behavior preserved, quality improved |

## How the Loop Works

```
┌─────────────┐     ┌──────────┐     ┌───────────┐
│ program.md  │────>│ Producer │────>│ Evaluator │
│ (what to do)│     │ (cooks)  │     │ (tastes)  │
└─────────────┘     └────┬─────┘     └─────┬─────┘
                         │                  │
┌─────────────┐          │   ┌──────────┐   │
│restrictions │──────────┼──>│loop-state│<──┘
│.md (quality │          │   │.md       │
│ gates)      │          │   │(history) │───> loops back
└─────────────┘          │   └──────────┘     to producer
                         v
                  ┌────────────┐
                  │  ./output/ │
                  │ (the dish) │
                  └────────────┘
```

1. **Producer** reads the program and previous feedback, then builds/writes/researches.
2. **Evaluator** scores the output against restrictions and success criteria.
3. **Loop state** captures structured feedback so the next iteration knows what to fix.
4. Repeats until the quality threshold is met or iterations are exhausted.

The loop stops early when **all hard constraints pass** AND the **score >= completion_threshold**.

## Tool-Specific Setup

### Claude Code

```bash
# Interactive (inside Claude Code)
/start-project ./my-task     # scaffold
/start-working ./my-task     # let him cook

# Headless (unattended)
letcook run ./my-task --tool claude

# With custom tool permissions
claude -p \
  "Read skill.md, program.md, and restrictions.md, then execute the autonomous loop." \
  --allowedTools "Read,Write,Edit,Bash,Glob,Grep,Agent" \
  --max-turns 200 \
  --max-budget-usd 10.00
```

**Claude Code `--allowedTools` reference:**

| Tool | What it does | When to include |
|------|-------------|-----------------|
| `Read` | Read files | Always |
| `Write` | Create/overwrite files | Always |
| `Edit` | Targeted file edits | Always |
| `Glob` | Find files by pattern | Always |
| `Grep` | Search file contents | Always |
| `Bash` | Run shell commands | `build`, `experiment` |
| `Agent` | Spawn subagents | For parallel producer/evaluator |
| `WebSearch` | Web search | `research` |
| `WebFetch` | Fetch URL content | `research` |
| `NotebookEdit` | Edit Jupyter notebooks | `experiment` |

Granular Bash: `--allowedTools "Bash(python *),Bash(pytest *)"` restricts which commands can run.

Install Claude Code skills globally:

```bash
ln -s ~/.letcook/integrations/claude/skills/start-project ~/.claude/skills/start-project
ln -s ~/.letcook/integrations/claude/skills/start-working ~/.claude/skills/start-working
```

### Cursor / Windsurf / Continue.dev

```bash
letcook init ./my-task --tool cursor    # or windsurf, continue
```

Open the project in your IDE. The rules auto-activate. Tell the AI:

> Start working on this project.

### Aider

```bash
letcook init ./my-task --tool aider
letcook run ./my-task --tool aider

# Or manually:
aider --read skill.md --read program.md --read restrictions.md \
  --message "Execute the autonomous loop as defined in skill.md."
```

### Any other tool

The universal prompt works with any AI assistant:

> Read skill.md, program.md, and restrictions.md, then execute the autonomous loop as defined in skill.md.

## Repository Structure

```
letcook/
├── bin/letcook                               # CLI binary
├── install.sh                                # One-liner install script
├── Makefile                                  # make install / uninstall / link
├── skill.md                                  # Execution engine (vendor-neutral)
├── templates/
│   ├── program.md                            # Task definition template
│   └── restrictions.md                       # Quality gates template
├── integrations/
│   ├── claude/skills/                        # Claude Code /start-project, /start-working
│   ├── cursor/autonomous-loop.mdc            # Cursor rules
│   ├── windsurf/autonomous-loop.md           # Windsurf rules
│   ├── continue/autonomous-loop.md           # Continue.dev rules
│   └── aider/.aider.conf.yml                 # Aider config
└── examples/
    ├── program.md                            # Example task
    └── restrictions.md                       # Example restrictions
```

## Acknowledgments

Inspired by Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch).
# Let-Cook
