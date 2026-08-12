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
- Both of the serious items here have the same shape, and it is not "we found
  bugs later". Both had already been checked, and the check is what gave the
  false confidence. The drift bug had a docstring, and the docstring was
  accurate: it stated that weights were held at their targets between
  rebalances. It described what the code did and nobody asked whether that was
  the right thing to do, so accurate documentation of wrong behaviour read
  exactly like correct behaviour. The app crashes had tests, and the tests
  passed - but every default selection in the app sits at five items or fewer,
  which is just below the threshold where the colour bug fires, so the suite
  was confirming that the defaults work rather than that the app works.
- What follows for me is that a check is only worth what its coverage is
  worth. Documentation verifies nothing on its own, and a green test suite
  says only that the cases it contains pass. Both failures needed a standard
  from outside the code to expose them.

## What I changed and why
I ordered both audits that found these problems, and neither would have
happened on the assistant's initiative. It had already finished this work and
considered it correct. I told it to read the Week 10 revision lecture in full
and then to check the build against the brief and that lecture line by line,
and that is the pass that turned up the drift accounting, the missing fear and
greed index, the missing discovery/holdout split, and the exhibit that did not
meet the "across methods" requirement.

I also refused the fix on inspection. The assistant's explanation of the drift
correction was convincing and I asked for identity checks with known answers
instead - a single-asset fund must reproduce its only holding, and period
growth must equal the weighted product of asset growth. Those are now
permanent tests rather than one-off confirmations.

## Frequency choice - my reading
Monthly stays the headline schedule, and the study is what lets me say that
rather than assume it. Quarterly loses everywhere, so the cost of carrying a
three-month-old covariance estimate is real. Above that floor the choice only
matters for the funds that actually move: equal weight and risk parity are
flat across every schedule because their weights barely change, while maximum
Sharpe turns over several times a year and is the one fund where the decision
has a price. Monthly is its best net-of-cost schedule, and it is within a few
hundredths of the best for every other fund, so it is the schedule that costs
least where it matters most. Weekly buys a fresher estimate that the extra
turnover does not repay - which is the same estimation-error argument from
Section 2 showing up in the trading decision rather than in the weights.
