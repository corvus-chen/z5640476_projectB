# Prompt log 01 - Part B setup and data foundation

## What I wanted
Start Part B: understand the Part B workflow, replace the placeholder
CLAUDE.md with my real working instructions, and migrate my Part A data
foundation (cleaning + return panels + headline alignment) into
`src/etl.py` and `src/features.py`.

## Prompt(s)
1. "I want to start on Project B - first explain the approach and process to
   me." (asked in Chinese; the assistant replied with the Station 3-4
   breakdown, the grading weights, and a build order)
2. "Continue" - proceed with the proposed first steps: write CLAUDE.md, then
   migrate the Part A pipeline.

## What the assistant produced
- A Part B work plan: migrate the Part A foundation, then portfolios +
  walk-forward OOS backtest, then the VADER sector sentiment index, then the
  fusion before/after, then the Streamlit app reading only precomputed CSVs.
- `CLAUDE.md`: my Part B working rules - data rules carried from Part A,
  Part B red lines (no look-ahead, sentiment lagged >= 1 trading day, the
  deployed app never imports nltk or recomputes backtests), the exact
  required output filenames, and candidate innovation extensions.
- `src/etl.py`: Part A cleaning rules as loud guards (2023-12-31 cap, unique
  ticker-date prices, news dedup on ticker+date+title, UTC -> tz-naive).
- `src/features.py`: long/wide daily returns from adjClose, per-panel
  returns first then left-merge crypto onto the equity calendar, headline
  alignment to same/next trading day.
- A smoke test that verified the row counts against the brief's data
  dictionary: equities 50,300 rows over 1,005 trading days; crypto
  14,610 = 14,620 - 10 stray 2024-01-01 rows; news 146,836 =
  149,683 - 2,847 exact duplicates; combined panel 1,005 x 60 with no
  missing values; 12,551 headlines moved to the next trading day and 6
  dropped past the last 2023 trading day.

## What was wrong or risky
- The assistant first wrote "30 rows dropped" in a docstring from memory of
  Part A; the smoke test showed the true count is 6, and it corrected the
  docstring. Unverified numbers must always be re-run, not recalled.
- The count itself was harmless in a docstring. What it would not have been
  harmless in is the report. My CLAUDE.md requires every number to trace back
  to the data or to a computation I can re-run, and a figure copied out of a
  docstring satisfies neither - I would have had no way of telling, later,
  whether "30" came from a measurement or from a recollection. The damage of
  this kind of error is not that it is large, it is that it is untraceable.
- The mistake was not misremembering Part A. The Part A figure was right for
  Part A; it was carried into Part B, where the alignment code differs and the
  answer is 6. Conclusions do not travel between projects even when the data
  and the author are the same.
- This belongs to the same family as the failures later in the project. The
  solver that silently returns its starting point, the docstring that
  accurately describes the wrong behaviour, the test suite that only exercises
  defaults, and this recalled number are all the same thing: something
  asserted without being checked against the data in front of it. The form
  changes and the cause does not.

## What I changed and why
I decided to reuse my own Part A foundation rather than rewrite it, which the
brief allows, but I attached a condition: everything carried over has to be
re-measured on this project's code path, not trusted because it was right
before. That condition is what produced the shape of `src/etl.py`. Part A's
cleaning rules are not re-implemented there as prose or as comments; they are
re-applied as guards that raise if the data no longer satisfies them - the
2023-12-31 cap, uniqueness on ticker and date, the balanced panel, the
deduplication on ticker plus date plus title. If the hosted data ever changes
under me, the pipeline stops rather than producing a quietly different answer.

The dropped-headline count is the small example of exactly the condition I had
set, arriving in the first hour of the project. The rule was already the right
one; what I learned is that it applies to the assistant's memory of my own
earlier work as much as to the data.

I also fixed the language rule at this point: everything in the folder -
code, comments, report, agent files, and these logs - is written in English,
with Chinese used only in conversation.
