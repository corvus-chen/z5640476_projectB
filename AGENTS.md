# AGENTS.md - z5640476, Part B

I built this project with Claude Code, so my working instructions live in the
files that tool reads:

- **`CLAUDE.md`** - the project rules: environment, the data rules carried over
  from my Part A, the Part B red lines (no look-ahead, sentiment lagged at
  least one trading day, the deployed app reads precomputed CSVs and loads no
  scoring library), the exact required output filenames, and how I want AI work
  logged.
- **`.claude/rules/`** - the three standards I made the assistant work to:
  `no-lookahead.md`, `verify-numbers.md`, and `my-words-not-yours.md`.
- **`.claude/skills/`** - three workflows I invoke by name rather than
  re-explaining: `audit-backtest`, `check-exhibit`, and `log-session`.
- **`ai/`** - eight prompt logs recording what I asked for, what came back,
  what was wrong, and what I decided. `ai/README.md` maps the whole pack.

This file exists because the starter includes one for Codex users. Anything an
agent needs to know about working in this folder is in `CLAUDE.md`; that file
and this one should not disagree, and if they ever do, `CLAUDE.md` is the one
I maintain.
