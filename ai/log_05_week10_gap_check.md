# Prompt log 05 - checking my build against the Week 10 revision lecture

## What I wanted
The Week 10 revision lecture is the lecturer's own worked Part B ("Overfit
Capital"). I had the assistant read all 56 pages and check my build against
it, rather than assume I had covered everything.

## Prompt(s)
"Read week10_revision_fins5545" (the PDF on my desktop).

## What the assistant produced
A point-by-point comparison. It confirmed the core structure matches the
reference implementation: 12 funds across three universes and four methods,
walk-forward backtest with 36 monthly rebalances from January 2021, rf = 0,
252/365 annualisation, the same tilt formula w~ = w_base(1 + lambda*z) with
clipping and renormalisation, a transaction-cost model, a finance lexicon, and
an app that loads precomputed files only.

It then found two real gaps and built both:

1. **Fear and greed index** (lecture pp. 32, 45, 54) - average sentiment
   across all 50 stocks, rescale to 0-100, standardise. My build reproduces
   the lecturer's own findings independently: the raw gauge sits above neutral
   on 99.0% of days (the lecture says 98%), and the deepest standardised
   troughs are March 2020 (the COVID crash) and 2 December 2021 (Omicron) -
   exactly the two episodes the lecture names.
2. **Discovery/holdout validation** (lecture pp. 40-41) - the lecture shows a
   tilt that topped tuning at Sharpe 0.84 and then fell to 0.08 on the holdout
   year. I applied the same protocol to my five variants: select on 2021-2022,
   report on 2023.

Holdout result: the adaptive tilt on the plain lexicon is what tuning selects
on 2021-2022 for BOTH equity funds, and it also ranks first on 2023 - it did
not collapse the way the lecture's example did.

| Fund | Variant | 2021-22 | 2023 |
|---|---|---|---|
| Min-Variance | adaptive / plain (selected) | 0.687 | 0.111 |
| Min-Variance | base | 0.655 | 0.072 |
| Max-Sharpe | adaptive / plain (selected) | 0.589 | 0.876 |
| Max-Sharpe | base | 0.495 | 0.809 |

## What was wrong or risky
- I had NOT built the fear and greed index at all. It appears three times in
  the lecture, including in the list of what a user should be able to do in
  the app, so leaving it out would have cost marks in two bands. Reading the
  lecture rather than trusting my own coverage is what caught it.
- The holdout margin over the base fund is small: +0.039 and +0.068 of a
  Sharpe point. That matches the lecture's own conclusion that a disciplined
  tilt leaves "a small edge out of sample", and I should not oversell it.
- Every Minimum-Variance variant decayed by about 0.57 of a Sharpe point into
  2023, base included. That is the market regime, not the tilt, and the report
  must say so rather than presenting the decay as a failure of the extension.
- Deliberate differences from the reference implementation I should defend in
  the report rather than quietly match: I use a ROLLING 252-day estimation
  window where the lecture uses an EXPANDING one, and my tilt z-score is
  cross-sectional across the ten sectors where the lecture standardises each
  stock over a rolling window. The brief allows both ("choose your own window
  type"), but I need to state the choice.
- [my own review notes go here]

## What I changed and why
[for me to fill in after I review the code]

## Verified references from the lecture
The lecture supplies the citations for the methods I use, which I can cite
with confidence because they come from the course itself: Markowitz (1952),
Sharpe (1966), Maillard, Roncalli and Teiletche (2010), DeMiguel, Garlappi and
Uppal (2009), Hutto and Gilbert (2014), Tetlock (2007), Baker and Wurgler
(2007), Moreira and Muir (2017). DeMiguel et al. is the one to cite for my own
finding that Equity Equal-Weight (Sharpe 0.817) beats every optimised equity
fund I built.
