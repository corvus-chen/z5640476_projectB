# Prompt log 08 - the course material, and replicating the reference implementation

## What I wanted
To close the loop on the Week 10 revision lecture. Log 05 used it as a
checklist and found four gaps. This entry asks the harder question: where do
my results agree with the lecturer's own worked example, where do they differ,
and can I account for the difference rather than explain it away.

## Prompt(s)
1. "Read the Week 10 revision lecture."
2. "Now compare against the teacher's requirements and the PDF - are there any
   problems?"
3. "Write our reflection on the lecture content and how it fed the build."

## The replication

The lecture reports Sharpe ratios for all twelve funds of its own reference
project. Mine differed, in one case enormously: Combined Maximum-Sharpe is
0.981 in my backtest against 0.40 in the lecture. A gap that size normally
means somebody has a bug.

It is not a bug. The lecture estimates on an EXPANDING window and I estimate
on a ROLLING 252-day one, and Appendix D of my report already runs both. Under
the lecture's window type my funds reproduce its numbers:

| Fund | Lecture | Mine, expanding | Difference |
|---|---|---|---|
| Combined Maximum-Sharpe | 0.40 | 0.398 | 0.002 |
| Combined Risk Parity | 0.78 | 0.777 | 0.003 |
| Combined Minimum-Variance | 0.61 | 0.589 | 0.021 |
| Equity Minimum-Variance | 0.62 | 0.589 | 0.031 |
| Equity Risk Parity | 0.75 | 0.717 | 0.033 |
| Equity Maximum-Sharpe | 0.72 | 0.663 | 0.057 |

Mean absolute difference 0.024. Equal weighting, which does not depend on the
window at all, comes out at 0.761 against the lecture's 0.76 on the combined
universe.

Two things follow. My implementation is right - independently coded, it lands
on the same numbers when the same design choice is made. And the single
largest discrepancy in the whole project, that Combined Maximum-Sharpe gap of
0.58, is entirely the window choice rather than an error, which is exactly
what Appendix D concluded from the other direction.

## Where the lecture shaped the build

- **Weights drift between rebalances.** The lecture states it in one line as
  real asset-management behaviour. My code applied fixed targets daily, which
  is arithmetically a fund that rebalances every day. Fixing it cost the best
  fund 0.05 of a Sharpe ratio it had never earned (log_06).
- **Rebalance frequency is a choice to test, not to assume.** The lecture
  suggests comparing weekly, fortnightly and monthly. Doing so showed
  quarterly is worst everywhere and that the schedule only matters for the
  funds whose weights actually move.
- **The fear and greed index.** Absent from my build entirely until the
  lecture named it. My version independently reproduces the lecturer's own two
  findings: the raw gauge reads above neutral on 99% of days, and the deepest
  standardised troughs are the March 2020 crash and the Omicron announcement.
- **Tuning on the past can overfit the future.** The lecture demonstrates a
  tilt that tops its tuning window at 0.84 and collapses to 0.08 out of
  sample. That slide is why my report re-picks the winning variant on
  2021-2022 alone and reports it on 2023.
- **Covariance shrinkage and extra optimisation methods** are listed as
  extension routes. The shrinkage study in Section 5.4 came from that list,
  though I used it to test my own diagnosis rather than to chase performance.

## Where I departed from it, and why

- **Rolling rather than expanding window.** Kept, and now defended with the
  replication above rather than with a preference. An expanding window helps
  the equity funds and costs the flagship combined fund 0.583 of a Sharpe
  point, because it never forgets the crypto regime that ended in 2022.
- **Cross-sectional rather than per-stock sentiment z-scores.** The tilt moves
  weight between sectors and takes no view on the market, so standardising
  across sectors on the day is the transformation that matches what it does.
- **A harder conclusion on sentiment.** The lecture finds a small edge from a
  mild tilt on its holdout. My lead-lag and horizon tests say the daily signal
  has no predictive content at all: sentiment correlates with same-day sector
  returns in seven of ten sectors and with next-day returns in one, and
  nothing survives correction across eight horizon specifications. I report
  the stronger negative because that is what my data shows, not because it
  contradicts the lecture.

## What was wrong or risky
- Treating the lecture as an answer key would have been the wrong use of it.
  Where my numbers differed I could have quietly adopted its window type and
  made the gap disappear; instead the difference became Appendix D and is now
  a result rather than an awkwardness. The replication is what makes the
  departure defensible - it shows I can hit the reference numbers and chose
  not to.
- The reverse risk is real too. Because the lecture is a course artefact and
  not a peer-reviewed source, its numbers are a sanity check on my
  implementation and nothing more. Agreement with it is not evidence that
  either of us is right about the market.
- One measurement in this entry needs care: the lecture's table is read off a
  slide, so the comparison is to two decimal places at best.

## What I changed and why
I ran the comparison rather than asserting my implementation was correct.
Before this, the only evidence that the backtest was right was that it passed
my own tests - and log_05 records what internal standards are worth. An
independent implementation of the same design landing within 0.024 of mine, on
average, is the first check in this project that came from outside it.
