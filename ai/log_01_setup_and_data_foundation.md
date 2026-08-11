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
- [my own review notes go here]

## What I changed and why
[for me to fill in after I review the code]
