---
name: audit-backtest
description: Audit a backtest or any new signal for look-ahead, survivorship, and accounting errors before its numbers are allowed into the report. Use whenever a component that estimates something from data is added or changed.
---

# Audit a backtest

Run this before any new number reaches the report. The point is to try to
break the result, not to confirm it.

## 1. Look-ahead

- Read the estimation slice. Does it end strictly before the decision date?
- Does anything estimated from data (correlation, threshold, direction,
  threshold, scaling) get fitted inside the walk-forward loop, or once on the
  full sample?
- Is every signal derived from text lagged at least one trading day, with
  smoothing applied before the shift?

Then prove it: add the component to `tests/test_no_lookahead.py` and confirm
truncation invariance. Reading the code is not evidence.

## 2. Accounting

- Do weights drift between rebalances, or are targets reapplied daily?
- Do weights sum to 1, and stay non-negative for a long-only fund?
- Is turnover measured from the DRIFTED holdings, not the previous target?
- Are equity and combined funds annualised on 252 and crypto-only on 365?
- Is the geometric annual return consistent with the Sharpe ratio's
  arithmetic mean, and if they diverge, is volatility drag the reason?

## 3. Identity checks

Cheap tests with a known answer catch more than inspection:

- A single-asset fund must reproduce that asset's returns exactly.
- Within one holding period, growth must equal `sum(w_i * prod(1 + r_i))`.
- Equal-weight targets should barely move; if turnover is large, drift
  accounting is wrong.

## 4. Selection

- Was this variant chosen by comparing several on the same data? If so, the
  ranking is fitted to that period. Re-select on a discovery window and report
  the pick on a holdout.
- How many variants were tried in total? Say the number in the report.

## Output

A short list: what was checked, what passed, what failed, and the exact
failing line. If everything passes, say which test file now covers it.
