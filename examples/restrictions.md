# Restrictions

## Hard Constraints

- Code must have type hints on all function signatures
- Functions must be under 30 lines
- Must run without errors on Python 3.10+
- No dependencies beyond stdlib + pygments

## Soft Constraints

- Has docstrings on public functions
- Handles malformed markdown gracefully (no crashes)
- Output HTML passes basic validation (no unclosed tags)

## Out of Scope

- Do not modify files outside the declared scope
- Do not add a web server or live-reload feature
- Do not bundle pygments CSS as a separate file — embed it inline
