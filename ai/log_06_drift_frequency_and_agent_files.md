1# Prompt log 06 - the weight-drift fix, rebalance frequency, and my agent files

## What I wanted
After checking my build against the brief and the Week 10 lecture, three gaps
were left. I asked for all three: fix the weight-drift accounting, add the
rebalance-frequency comparison the lecture suggests, and build the `.claude/`
skills and rules the AI-workflow band asks for.

## Prompt(s)
1. "Now compare against the teacher's requirements and the PDF - are there any
   problems?"
2. "Go ahead" - fix the three gaps it found.

## What the assistant produced

**A required exhibit that did not meet spec.** The brief asks for a
portfolio-weights-over-time figure "across methods"; mine covered one method.
Added `weights_combined_across_methods.png`, three methods side by side on one
sector colouring.

**The weight-drift fix.** `oos_backtest` applied the same target weights to
every day between rebalances, which is arithmetically a fund that trades back
to target DAILY - the opposite of rebalancing monthly, and it collects a
rebalancing bonus the fund never earned. Now the value of $1 inside a holding
period is `sum_i w_i * prod(1 + r_i)` and the daily return is the change in
that value. Turnover is measured from the drifted holdings rather than the
previous target, and the cost model charges on that.

Effect on the combined funds (Sharpe, before -> after):

| method | before | after |
|---|---|---|
| Equal-Weight | 0.763 | 0.761 |
| Minimum-Variance | 0.491 | 0.477 |
| Maximum-Sharpe | 1.034 | 0.981 |
| Risk Parity | 0.896 | 0.888 |

Every headline number fell, most at Maximum-Sharpe, which is the fund whose
weights move most - exactly where a spurious rebalancing bonus would show up.

**The rebalance-frequency study.** Four schedules across the four methods,
gross and net of 10 bp. Quarterly is worst for every method. Best net schedule
differs by method: fortnightly for Equal-Weight and Risk Parity, monthly for
Maximum-Sharpe, weekly for Minimum-Variance. Annual turnover ranges from 0.27
(Equal-Weight quarterly) to 7.7 (Maximum-Sharpe weekly), so costs bite very
unevenly.

**Agent files.** `.claude/rules/` (no-lookahead, verify-numbers,
my-words-not-yours) and `.claude/skills/` (audit-backtest, check-exhibit,
log-session), plus a pointer to them from CLAUDE.md.

## What was wrong or risky
- The drift bug was mine to catch, not the assistant's - it wrote the
  constant-weight version, documented it honestly as "no drift model", and I
  only found it by reading the lecture slide that describes drift as real
  asset-management behaviour. Documented wrong is still wrong.
- I did not accept the fix on inspection. Three identity checks:
  a single-asset fund must reproduce that asset exactly (max error 1.1e-16),
  period growth must equal `sum(w_i * prod(1+r_i))`, and drifted weights must
  sum to one and actually differ from targets (max drift 7.3 percentage
  points). All three are now in `tests/test_backtest_mechanics.py`.
- Every conclusion survived the fix - the adaptive tilt is still what tuning
  selects on 2021-2022 and still ranks first on the 2023 holdout. If the
  ranking had flipped, the earlier result would have been an artefact of the
  accounting error.
- Three latent app crashes found in the same pass: charts sized their colour
  list with a five-slot slice, so selecting six funds, six blended funds, or
  six sectors each raised StreamlitColorLengthError. My tests had only ever
  exercised the defaults, which all sit at five or fewer. Fixed, and
  `tests/test_app_charts.py` now maxes out every selection.
- Two figures had burst past A4 width because explanatory prose was appended
  to the source footer, which never wraps.
- [my own review notes go here]

## What I changed and why
[for me to fill in after I review the code]

## Frequency choice - my reading
Monthly stays the headline schedule. [my own justification goes here - the
study is in results/tables/rebalance_frequency.csv]
