---
name: start-working
description: Execute the autonomous producer/evaluator loop. Reads program.md and restrictions.md from the working directory, then iterates until the quality threshold is met or iterations are exhausted.
argument-hint: [path/to/directory]
---

Execute the autonomous loop.

Load the skill definition below and follow it exactly:

!`cat skill.md`

**Working directory**: Use `$ARGUMENTS` if provided, otherwise use the current directory.
**Program**: Read `program.md` from the working directory.
**Restrictions**: Read `restrictions.md` from the working directory.

Begin execution immediately. Do not ask the human for confirmation.
