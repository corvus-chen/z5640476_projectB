# Revision checklist (planning aid - not a deliverable)

Every passage below is interpretive prose the assistant drafted at my request
and I have not yet rewritten. The course grades my economic reasoning, so a
passage is only finished once it says what I think, in my words.

Edit `scripts/report_prose.py` and re-run
`python scripts/build_report_scaffold.py`, or edit `report/report.docx`
directly and stop running the script. Do not do both.

Tick a box only after rewriting, not after reading.

## How to rewrite a passage

Read the exhibit it sits under, decide what you think it shows, then write
that. If your conclusion differs from the draft, the draft is wrong, not you -
it was written from the numbers, not from judgment. Delete anything you cannot
defend if a marker asks "how do you know?".

## Section 1 - funds and backtest design

- [ ] `design_choices` - why a rolling window, monthly rebalancing, long-only
- [ ] `frequency` - why quarterly loses everywhere and why monthly is kept
- [ ] Still owed entirely by me: the four objective equations, numbered, with
      every symbol defined. The draft does not contain them.

## Section 2 - out-of-sample results

- [x] `metrics_table` - DONE. I chose the two-cause reading and the term
      "sample noise"; the DeMiguel estimation-window figure and the
      shrinkage bridge were added on that basis. Paragraph on minimum
      variance rewritten to my 'different investor, not a failure' position.
      Remaining: read the DeMiguel paper before the citation is final.
- [ ] `growth` - which fund an investor would have preferred, and the path
- [ ] `sharpe_bar` - families compared, and the equal-weight result
- [ ] `drawdown` - what the worst episode felt like
- [ ] `weights` - why each objective produces the picture it does

## Section 3 - sentiment index

- [ ] `sentiment_index` - the positive baseline, and what the sector ordering
      does and does not mean
- [ ] `fear_greed` - why the raw level is uninformative; the March 2020 and
      December 2021 troughs
- [ ] `coverage` - what the neutral share implies about headlines as a proxy

## Section 4 - fusion

- [ ] `fusion_table` - lower return plus higher turnover as the signature of a
      signal with no content
- [ ] `lead_lag` - the "already priced" reading over the reversal reading.
      **Check I agree with this before keeping it - it is the central claim of
      the section.**
- [ ] `horizons` - a null result with a suggestive shape; declare the eight
      specifications searched

## Section 5 - extensions

- [ ] `shrinkage` (5.4) - the Ledoit-Wolf test of the sample-noise diagnosis.
      Written after I asked for the test; the reading of WHY each method
      responds differently is still the assistant's wording.

- [ ] `lexicon` - which headlines were being missed; why a lower neutral share
      is not automatically a better signal
- [ ] `significance` - the intervals span zero, so the improvement is not
      established. **Do not let a rewrite soften this.**
- [ ] `holdout` - the ranking survived, with three caveats
- [ ] `design_system` - why colour validation matters for this product

## Section 6 - the app

- [ ] `app` - target user and journey. **Also still owed by me: the live URL,
      the public repository link, and one or two screenshots.**

## Section 7 - reflection

- [ ] `reflection` - what worked, what did not, and the broader lesson
- [ ] `recommendations` - the three recommendations. **These are judgment
      calls about a product I designed; they are the least defensible as
      someone else's words.**

## Section 8 - references

- [ ] `references_note` - verify each citation against the actual paper before
      it enters the bibliography. The list came from the Week 10 lecture, not
      from my own reading.

## Facts to check while rewriting

- The volatility-drag arithmetic in `metrics_table` is stated as an
  approximation. Confirm the numbers still match the current run.
- `weights` claims minimum variance concentrates in the sectors with the
  lowest estimated covariance. That is asserted, not measured - either check
  it or soften the claim.
- `sharpe_bar` says mixing crypto with equities lowered the Sharpe ratio
  relative to crypto alone. Verify against the metrics table.
- `holdout` quotes specific holdout Sharpe ratios pulled from the table at
  build time; they change if the pipeline is re-run.
