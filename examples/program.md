---
type: build
iterations: 5
completion_threshold: 90
output: ./output/
scope:
  - ./output/
---

## Goal

Build a Python CLI tool that converts a markdown file to a clean HTML page with syntax-highlighted code blocks. The tool should read from stdin or a file argument and write HTML to stdout.

## Context

- Use only the Python standard library plus `pygments` for syntax highlighting.
- The output HTML should be a complete document (doctype, head, body) with embedded CSS.
- Target Python 3.10+.

## Success Criteria

- [ ] (hard) Accepts a file path argument or reads from stdin
- [ ] (hard) Produces valid HTML5 output
- [ ] (hard) Code blocks are syntax-highlighted via pygments
- [ ] (soft) Handles tables, lists, blockquotes, and inline formatting
- [ ] (soft) Embedded CSS produces a readable, clean layout
- [ ] (soft) Includes a `--theme` flag to switch pygments styles

## Notes

- Keep it to a single file if possible.
- Include a shebang line so it can be run as `./md2html.py input.md`.
