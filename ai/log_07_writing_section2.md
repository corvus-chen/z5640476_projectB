# Prompt log 07 - interpreting the fund results and drafting the report

## What I wanted
To settle the main interpretive question of the results section - why equal
weighting beats every optimised equity fund - and then to get a complete
draft of the report onto the page so that I could revise against something
rather than a blank document.

## Prompt(s)
1. "Start the write-up for section 2."
2. "Which result should I interpret first?"
3. "Put it straight into the document, not as a draft - do as much as you can
   and I will revise it by hand at the end."

## What I directed, and what the assistant did

I would not accept an interpretation the assistant simply asserted, so I had
it turn the question into one the data could settle. It produced a diagnostic
I had not asked for by name: alongside the Sharpe ratio it reported each equity
fund's achieved volatility, turnover, holdings count, and weight instability -
the mean one-way change in the TARGET weights between rebalances, which
measures how much the optimiser's own answer moves when re-estimated.

| Method | Sharpe | Ann. vol | Turnover | Holdings | Weight instability |
|---|---|---|---|---|---|
| Equal-Weight | 0.819 | 0.161 | 0.027 | 50 | 0.000 |
| Risk Parity | 0.723 | 0.145 | 0.032 | 50 | 0.020 |
| Maximum-Sharpe | 0.573 | 0.182 | 0.331 | 6 | 0.342 |
| Minimum-Variance | 0.479 | 0.127 | 0.151 | 18 | 0.151 |

It also checked whether each method achieved its OWN objective. Minimum
variance does: the lowest volatility (12.7%) and the shallowest drawdown
(15.3%) of the four funds.

It then set out three competing readings with the supporting and contradicting
evidence attached to each and left the choice to me. **The interpretation in
the report is the one I chose**: two independent causes, where estimation error
explains the concentration and churn of maximum Sharpe and minimum variance,
while minimum variance ranking last on the Sharpe ratio is a mismatch between
its objective and the yardstick rather than a failure of the method. I chose it
because the single-cause reading is contradicted by the data - minimum variance
estimates fewer parameters than maximum Sharpe and still scores lower.

**The assistant then drafted the interpretive prose for the whole report, at my
instruction, and it is its wording and not mine until I rewrite it.** That
prose lives in `scripts/report_prose.py`, keyed by where each passage sits, and
`scripts/build_report_scaffold.py` renders it into `report/report.docx` along
with the structure, the thirteen exhibits and the ten tables. The report runs to
about 4,490 words of narrative.

`report/REVISION_CHECKLIST.md` lists all nineteen passages with a box against
each. Rewriting them is the outstanding work on this report, and the checklist
records which are done.

## What was wrong or risky
- The "estimation error" reading does not survive the data on its own:
  minimum variance estimates fewer parameters than maximum Sharpe and scores
  lower (0.479 against 0.573). That contradiction is what forced the two-cause
  reading, and it belongs in the report rather than a tidier single mechanism.
- Commissioning a full draft is a real risk to guard. Prose written from the
  numbers reads plausibly whether or not it is right, and it is easy to accept
  a paragraph because it is fluent. The checklist exists so that each passage
  has to be actively defended rather than passively kept.
- Three claims in the draft are asserted rather than measured, and I flagged
  them for checking: that minimum variance concentrates in the sectors with
  the lowest estimated covariance; that mixing crypto with equities lowered
  the Sharpe ratio against crypto alone; and a prediction that covariance
  shrinkage would narrow the gap, which this project never tests.
- The weight-instability measure is the assistant's construction, not a
  standard statistic. It has to be defined explicitly in the report for a
  reader to reproduce it.
- The DeMiguel, Garlappi and Uppal (2009) citation came from the Week 10
  lecture's reference list, not from my own reading. Verify the paper's actual
  finding before it enters the bibliography.
- The risk I am carrying knowingly is that fluent prose written from correct
  numbers reads as though it were reasoned, whether or not I have reasoned it.
  Nothing in the document marks which passages are mine, so the checklist and
  the proportion recorded below are the only record of that, and they are only
  worth anything if I keep them accurate as I work.

## What I changed and why

I worked through the report in Word rather than through the prose file. A
paragraph-by-paragraph comparison against the assistant's original draft puts
the current state at 15 of 46 substantial passages materially rewritten, ten
of them heavily; the remaining 31 still carry its wording. That measurement is
in this entry because I would rather state the proportion than imply a
completeness I have not reached.

The reasoning in Section 2 is mine. I rejected the "estimation error" framing
and replaced it with sample noise, because the problem is the size of the
sample rather than a fault in the estimator: 252 days asked to produce 50
expected returns and a 50-by-50 covariance matrix. I took the two-cause
reading of the method ordering over the single-cause one, because the
single-cause version is contradicted by minimum variance scoring below maximum
Sharpe on fewer estimated parameters. And I settled the minimum-variance
paragraph on my own position - the fund is not a failure but a product for a
different investor, which is also why the app lists all twelve funds rather
than only the top of the Sharpe table.

Working in Word I then added the citation layer that the draft did not have:
Michaud (1989) on error maximisation and Chopra and Ziemba (1993) on
expected-return errors being roughly an order of magnitude more costly than
variance errors, which together turn Section 2 from an assertion about noise
into an argument with a mechanism; Loughran and McDonald (2011) on
out-of-domain dictionaries misclassifying financial language; Tetlock,
Saar-Tsechansky and Macskassy (2008) on full stories rather than headlines;
Bailey and Lopez de Prado (2014) and Harvey, Liu and Zhu (2016) on what a
maximum Sharpe ratio means once the number of trials is counted; Da, Engelberg
and Gao (2015), Fama (1970), Boudoukh et al. (2008), and Okabe and Ito (2008)
elsewhere. Several of those passages were rewritten around the citation rather
than having it appended, which is why they now differ most from the draft.

What is still the assistant's wording is listed in
`report/REVISION_CHECKLIST.md`, and the passages I would most want in my own
words before submission are the three recommendations and the reflection in
Section 7, since those are judgments about a product I designed.
