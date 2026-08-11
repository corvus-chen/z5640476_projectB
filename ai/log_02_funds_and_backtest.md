# Prompt log 02 - funds, backtest engine, and the no-look-ahead test

## What I wanted
The Station 3 fund engine: several optimisation methods, a walk-forward
out-of-sample backtest with no look-ahead, and the twelve (family, method)
funds with their performance metrics.

## Prompt(s)
"Build portfolios.py: optimisers plus a walk-forward OOS backtest. Rebalance
monthly, weights from past data only, annualise 252 for equity and combined
and 365 for crypto, and sanity-check that weights actually differ across
methods."

## What the assistant produced
- `optimise_weights` for equal-weight, minimum-variance, maximum-Sharpe, and
  risk parity, solved with SLSQP under long-only, fully-invested constraints.
- `oos_backtest`: rebalance on the first trading day of each month, estimate
  on the 252 days strictly before the rebalance date, hold the targets until
  the next rebalance.
- `build_funds` / `metrics_table` for the twelve funds, and
  `tests/test_no_lookahead.py`, which reruns every fund on a sample truncated
  at 30 June 2022 and requires the pre-cut returns and weights to match the
  full-sample run exactly.

Results (out-of-sample, from 4 January 2021): Combined Maximum-Sharpe has the
best Sharpe at 1.03; Combined Minimum-Variance the lowest drawdown at -15.6%;
Crypto Maximum-Sharpe loses money, at -26.3% a year.

## What was wrong or risky
- The brief warns that solvers stall on daily-return covariances (~1e-4),
  below SLSQP's default tolerance, and silently return the equal-weight
  starting point. The first version optimised on raw daily moments. I had it
  scale mean and covariance by 252 before solving and then checked the
  pairwise weight differences across methods: the largest gap is 0.44, and
  the methods hold 60 / 19 / 8 / 60 assets, so the solver genuinely moves.
- Crypto Maximum-Sharpe reports a geometric annual return of -26.3% but a
  Sharpe of +0.01. That looked like a bug. It is the volatility drag: at 79%
  annualised volatility the arithmetic mean (+1.1%) and the geometric mean
  diverge sharply. The fix was reporting both, not changing the formula.
- [my own review notes go here]

## What I changed and why
[for me to fill in after I review the code]
