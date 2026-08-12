# Prompt log 04 - the innovation extensions

## What I wanted
The extensions that carry the Innovation criterion (30% of Part B). I asked
the assistant which direction it thought was strongest before committing,
rather than taking the first idea.

## Prompt(s)
1. "Which extension is better?" - after it laid out four candidates (finance
   lexicon, adaptive tilt direction, transaction costs, reusing the Part A
   attention measure).
2. "Build it."

## What the assistant produced and argued
Its recommendation, which I took: make the ADAPTIVE-DIRECTION TILT the primary
extension and the finance lexicon the companion. The argument was that the
brief names lexicon extension twice as an example (Sections 1 and 5), so every
student who prompts an AI will produce it, whereas the adaptive tilt comes out
of my own diagnostic finding - eight of ten sectors show a NEGATIVE
correlation between lagged sentiment and the return it can be traded on. It
also advised dropping the Part A attention measure here as recycling.

Built:
- `src/finance_lexicon.py` - 46 terms with a score, a category, and a written
  rationale each, selected by frequency FROM THE HEADLINES rather than from
  memory, plus an `EXCLUDED` list of ambiguous terms with reasons.
- `fusion.make_adaptive_sentiment_tilt` - re-estimates the pooled sentiment /
  return correlation at each rebalance from the prior 252 days only and takes
  the sign of that estimate as the tilt direction.
- `fusion.apply_costs` - 10 bp of one-way turnover charged at each rebalance.
- `tests/test_no_lookahead.py::test_adaptive_tilt_is_truncation_invariant`.

Measured results (out-of-sample, equity funds):

| Variant | Min-Var Sharpe | Max-Sharpe Sharpe |
|---|---|---|
| base (no sentiment) | 0.487 | 0.586 |
| fixed tilt / plain lexicon | 0.464 | 0.522 |
| adaptive tilt / plain lexicon | **0.520** | **0.673** |
| fixed tilt / extended lexicon | 0.509 | 0.572 |
| adaptive tilt / extended lexicon | 0.398 | 0.553 |

The lexicon cut the neutral share from 49.6% to 43.4% and rescored 16.1% of
headlines. The adaptive tilt beat the base fund on both funds and still beat
it after transaction costs (0.650 against 0.565 on Maximum-Sharpe).

## What was wrong or risky
- The biggest risk was the adaptive tilt smuggling in look-ahead, since it
  estimates a relationship from data. I did not accept it until the truncation
  test covered it: run the fund on the full sample and on a sample cut at 30
  June 2022, and require identical pre-cut weights and returns. It passes.
- The direction came out -1 at all 36 rebalances. That means the outcome is
  numerically close to hard-coding a contrarian tilt, and a marker could say
  so. The honest defence is that the sign was ESTIMATED from past data every
  time and would have flipped had the window said otherwise - not that the
  mechanism was never tested. The pooled correlation is also tiny (-0.047 to
  -0.002), so the relationship is weak even where it is consistent.
- The assistant initially wanted to score every frequent finance word. I had
  it exclude the ambiguous ones instead ('cut' reverses between a dividend cut
  and a rate cut; 'buy' is 15,806 listicle headlines about the writer, not the
  company). Fewer words with reasons beats more words without.
- The lexicon scores are AI-proposed. The brief allows exactly this workflow,
  but the file carries a [HUMAN EDIT REQUIRED] marker until I have gone
  through the 46 entries myself.
- One honest limitation the assistant surfaced rather than hid: "Inovio's
  Surge on a Coronavirus Vaccine Was Just Speculation" scores +0.53 under the
  extended lexicon because 'surge' fires, though the headline is sceptical.
  Headline-level scoring cannot read that.
- Reading the best of five variants off one out-of-sample period is itself a
  selection effect. It belongs in the report as a caveat, not as a claim.
- The -1 direction at all 36 rebalances is the item I now weigh most heavily,
  and my defence of it at the time was weaker than I thought. Saying the sign
  would have flipped had the window said otherwise is a claim about a branch
  of the code that never executed on this data. The mechanism is correct and
  the truncation test proves it never looks forward, but on this sample it was
  never exercised in both directions, and that is a limitation of the evidence
  rather than a point in the method's favour.
- The numbers in this entry predate the weight-drift fix in log_06 and no
  longer match results/. They are left as recorded.

## What I changed and why
I chose the adaptive tilt over the lexicon extension as the primary
innovation, against the assistant's initial framing, because the lexicon is
named twice in the brief as an example and would therefore be the crowded
choice, while the adaptive tilt came out of a diagnostic in my own data. I
also cut the lexicon down: the assistant proposed scoring every frequent
finance term and I had it exclude the ones whose sign reverses with context,
on the grounds that a smaller list I can defend beats a longer one I cannot.

## How I would rate this extension now
Two things are true about the adaptive tilt and neither is "it worked".

It is methodologically sound and cannot be shown to be effective. The design
is right - the direction is estimated walk-forward from past data only, the
truncation test covers it, and the result is reported gross and net of costs.
The result is a Sharpe improvement whose bootstrap interval spans zero
(p = 0.337 and 0.749), on a relationship that the later lead-lag test shows is
mostly noise. So the value sits in the process rather than the outcome:
building it correctly, and then reporting honestly that three years of daily
data cannot establish it, is the part I would defend.

Its larger contribution was to expose problems rather than to solve one.
Building it is what made me ask whether the improvement was bigger than noise,
which produced the bootstrap test; and asking why it worked at all is what
produced the lead-lag test, which overturned the contrarian explanation I had
been carrying since log_03. Neither of those checks would exist if I had
stopped at the naive tilt and its negative result. The extension earned its
place by generating the tests that showed the rest of my reasoning to be
wrong.

## The interaction between the two extensions - my reading
The two extensions do not stack: the lexicon helps the fixed tilt (0.522 to
0.572 on Maximum-Sharpe) but hurts the adaptive one (0.673 to 0.553). The
diagnostics show why - the extended lexicon weakens the very contrarian
relationship the adaptive tilt trades, with the mean correlation moving from
-0.0205 to -0.0156 and the count of negative sectors from 8/10 to 7/10.

Read alongside the lead-lag result, that interaction is less puzzling than it
first looked. Part of what the adaptive tilt was trading was VADER's blind
spots rather than a property of the news, so making the sentiment measurement
more faithful removed some of the very thing the tilt was leaning on. An edge
that shrinks when the input is improved was probably not an edge in the
market.
