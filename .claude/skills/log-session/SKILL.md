---
name: log-session
description: Draft the factual half of a prompt-log entry in ai/ after a piece of work, leaving my judgment sections empty. Use at the end of any task that produced code or numbers.
---

# Draft a prompt log entry

The AI workflow is 20% of Part B and the marks are for judgment, not for
volume. A good entry reads like a short story about a problem: I asked for X,
the assistant did Y, Y was wrong in this specific way, I did Z instead.

Write to `ai/log_NN_<task>.md`, numbered after the last existing log.

## Sections you fill in

**What I wanted** - the goal in one or two sentences.

**Prompt(s)** - what I actually asked, in English, verbatim where possible. Do
not tidy my prompt into something more articulate than it was.

**What the assistant produced** - a factual summary: files, functions, and the
measured numbers with enough precision to re-check. Include the numbers that
turned out to be wrong, not only the final ones.

## Sections you leave EMPTY

**What was wrong or risky** - list the concrete defects you know about
factually (a crash, a wrong count, a violated rule), then leave
`[my own review notes go here]`. Do not editorialise about severity.

**What I changed and why** - leave `[for me to fill in after I review]`
entirely. This is the graded reflection and it must be mine.

**Any interpretation of results** - leave a marked placeholder.

## What makes an entry worth marks

- A specific mistake with its fix, not "the AI helped me build the backtest".
- The check that caught it, named.
- Numbers before and after.
- Times the assistant was told to stop or do it differently.

Do not write entries that make the process look smooth. The failures are the
evidence that I was directing rather than pasting.
