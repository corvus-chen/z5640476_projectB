# AI workflow pack (z5640476, Part B)

Everything the course asks me to submit about how I directed and checked AI on
this project, and where to find each piece.

## What is here, and what it is for

| Evidence | Where |
|---|---|
| My agent instruction file | `../CLAUDE.md` at the project root |
| My rules - the standards I made the assistant work to | `../.claude/rules/` |
| My skills - the workflows I invoke rather than re-explain | `../.claude/skills/` |
| Prompt logs, one per stage of the build | `log_01` to `log_07` in this folder |
| Iteration history - every change with its reason | the commit history, see below |

`prompt_log_template.md` is the starter's template, kept for reference.

## The rules I set

`../.claude/rules/` holds the three standards the assistant had to work to,
each written after I saw why it was needed:

- `no-lookahead.md` - the one rule I would not accept a violation of, and the
  truncation test that has to prove compliance rather than an argument that it
  complies.
- `verify-numbers.md` - no statistic from memory, including the assistant's
  memory of its own earlier work. Written after it wrote "30 rows dropped"
  from recollection when the measured answer was 6 (log_01).
- `my-words-not-yours.md` - where the assistant stops and my own economic
  interpretation begins.

`../.claude/skills/` holds three workflows I invoke by name: `audit-backtest`
before any new number reaches the report, `check-exhibit` after any figure
changes, and `log-session` to draft the factual half of an entry here.

## Iteration history

The version history is the record of how the project actually developed, and
it is not visible in the zip. It is in the public repository:

**https://github.com/corvus-chen/z5640476_projectB/commits/main**

Each commit message states what changed and why. The ones that matter most are
the corrections: the weight-drift accounting fix, the trim to the word limit,
and the addition of the rolling-versus-expanding window study.

## How to read the logs

Each entry separates what the assistant produced from what I judged. The
factual sections record prompts, output, and measurements; the sections headed
"What was wrong or risky" and "What I changed and why" are mine.

Read in order, they describe one recurring failure rather than seven separate
ones. Every serious error in this project was a failure of verification rather
than of modelling:

- a number recalled instead of measured (log_01)
- a solver that silently returns its starting point (log_02)
- an explanation that fitted all the evidence because it had never been tested
  against a rival (log_03)
- an extension whose value turned out to be the tests it forced me to run
  (log_04)
- gaps that no internal check could find, because every standard I was
  checking against came from inside the project (log_05)
- a docstring that accurately described the wrong behaviour, and a test suite
  that only ever exercised the defaults (log_06)
- prose that reads as reasoned whether or not it was reasoned (log_07)

log_08 closes the loop from the other side. Re-running my funds on the
lecture's expanding window reproduces its published Sharpe ratios to within
0.024 on average, and to 0.002 on the fund where our headline numbers differ
most. That is the first check in this project whose standard came from outside
it.

`../report/REVISION_CHECKLIST.md` tracks the passages of the report that are
still the assistant's wording rather than mine.
