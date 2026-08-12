# Revision checklist (planning aid - not a deliverable)

Every passage below is interpretive prose the assistant drafted at my request
and I have not yet rewritten. The course grades my economic reasoning, so a
passage is only finished once it says what I think, in my words.

Tick a box only after rewriting, not after reading.

## STOP - read this before touching anything (state as of 11 Aug, 23:50)

**`report/report.docx` is now the single source of truth. Do NOT run
`python scripts/build_report_scaffold.py` again - it would overwrite the
citations I added in Word.** `scripts/report_prose.py` is now historical: it
holds the assistant's original draft, not what is in the document.

The old pre-citation version is recoverable from git commit `38e6871` if
anything goes wrong.

### Open problem: the report is over the word limit

| | words |
|---|---|
| Narrative as counted | 5,508 |
| less the auto-generated Contents field | -131 |
| **Real narrative** | **~5,377** |
| Limit | 5,000 |
| **Over by** | **~377** |

References and the Appendix do not count. The two heaviest sections are
Section 5 (1,339) and Section 2 (1,123), together 46% of the narrative.

### Trim plan, ready to execute (paragraph indices from python-docx)

1. **Move all of 5.5 "The figure design system" to the Appendix** - paragraphs
   126 (93w) and 127 (65w). Saves ~158. It is the least central extension and
   reads naturally as an appendix note.
2. **Paragraph 44** (241w, "The first is sample noise") - now the longest in
   the report after I added Michaud and Chopra-Ziemba. The mechanism is
   explained again in 5.4; cut the overlap here and keep the citations.
   Target ~60.
3. **Paragraph 119** (135w, "Three caveats belong with that") - three caveats
   stated at length; the third repeats the bootstrap point from 5.2.
   Target ~40.
4. **Paragraph 61** (126w, the three weights panels) - describes what the
   figure already shows. Target ~30.
5. **Paragraph 73** (160w, neutral share) and **paragraph 71** (141w, raw
   gauge) in Section 3 - both restate their exhibits. Target ~50 between them.

That totals roughly 340. The remainder can come from anywhere in Section 5.

### New citations I added and still have to verify

- **Michaud (1989)**, the error-maximisation property.
- **Chopra and Ziemba (1993)**, errors in expected returns being about an
  order of magnitude more costly than errors in variances.

Both are load-bearing in paragraph 44 now. Confirm the exact claims and the
publication details before the bibliography is final.

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

- [x] `metrics_table` - DONE, and extended in Word. I chose the two-cause
      reading and the term "sample noise"; the DeMiguel estimation-window
      figure and the shrinkage bridge followed from that. The minimum-variance
      paragraph is my 'different investor, not a failure' position. In Word I
      then added Michaud (1989) on error maximisation and Chopra and Ziemba
      (1993) on the relative cost of mean versus variance errors, which is the
      strongest passage in the report and the one that now needs trimming
      rather than expanding.
      Remaining: verify DeMiguel, Michaud, and Chopra-Ziemba against the
      papers themselves.
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
