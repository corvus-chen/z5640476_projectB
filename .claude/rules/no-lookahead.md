# Rule: no look-ahead, and prove it

The single rule I will not accept a violation of. Every number an investor
sees in Spotlight must have been earnable at the time.

## What the assistant must do

- Weights at a rebalance on date `t` come from returns strictly BEFORE `t`.
  `panel.iloc[pos - window:pos]`, never `pos + 1` and never a slice that
  includes `t` itself.
- Sentiment used for a decision on `t` comes from `t-1` or earlier. Smoothing
  happens BEFORE the lag, never after - a centred or trailing window applied
  after shifting reintroduces future information.
- Anything estimated from data (a correlation, a threshold, a tilt direction)
  is re-estimated inside the walk-forward loop from the window only. Fitting
  it once on the full sample and reusing it is look-ahead even when the code
  looks innocent.
- Between rebalances the weights DRIFT with prices. Applying fixed target
  weights to every day silently assumes daily rebalancing and pays the fund a
  rebalancing bonus it never earned.

## How it gets proved

Assertion, not inspection. The test is truncation invariance: run the fund on
the full sample, run it again on the sample cut short, and require the
overlapping returns AND weights to match exactly. A backtest that peeks
cannot pass.

`tests/test_no_lookahead.py` holds this for every method and for the adaptive
tilt. Any new component that estimates something must be added to it in the
same commit, not later.

## What I want said out loud

If a request would require look-ahead to answer, say so and refuse the shortcut
rather than quietly producing a number. Tell me which specific line is the
risk, not a general warning.
