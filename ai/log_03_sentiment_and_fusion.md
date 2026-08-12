# Prompt log 03 - sentiment index, fusion, and the app

## What I wanted
The Station 3 sentiment model (VADER to a sector index), the fusion of that
index into the equity funds, and the Station 4 Streamlit app.

## Prompt(s)
1. "Build sentiment.py: score the raw headlines with VADER, aggregate to
   ticker-day, equal-weight within sector, justify how no-headline days are
   treated, and lag at least one trading day."
2. "Build fusion.py: a look-ahead-safe sentiment tilt on the equity funds with
   a before-vs-after table."
3. "Build the Streamlit app for the investor journey - compare funds, fact
   sheet, allocation, sentiment - reading only precomputed CSVs."

## What the assistant produced
- `sentiment.py`: raw-text VADER scoring, ticker-day means, an equal-weight
  sector index carrying raw, 5-day smoothed, and one-day-lagged columns, plus
  a coverage table. No-headline ticker-days are dropped from the sector mean
  rather than scored zero.
- `fusion.py`: a cross-sectional sector tilt,
  `w_tilted = w_base * (1 + strength * z_sector)`, clipped and renormalised,
  wired into the same backtest engine through a `tilt_fn` hook so the base and
  tilted funds share identical mechanics.
- `streamlit_app.py`: four tabs (compare, fact sheet, allocation, sentiment)
  reading only the committed CSVs.

Numbers: 146,830 headlines scored, 49.6% neutral. The tilt LOSES to the base
fund - Equity Minimum-Variance Sharpe falls 0.487 to 0.464, Equity
Maximum-Sharpe 0.587 to 0.522, with turnover rising in both.

## What was wrong or risky
- The lag had to be checked, not assumed. I asserted that
  `sentiment_lagged[t] == sentiment_smoothed[t-1]` for all ten sectors and it
  passed. Smoothing is applied BEFORE the shift, so the smoothed value on
  day t never contains day-t information.
- The assistant's first figure call crashed (`new_figure` returns an axis
  array, not a single axis) and its first sentiment chart used a 5-day mean,
  which was unreadable with five sectors on one panel. Fixed to 21 days for
  the exhibit, with the daily series kept in the CSV.
- Two direct labels overlapped in the growth-of-$1 figure ($1.52 and $1.48).
  Added a label de-collision helper rather than leaving overlapping text.
- Risk to remember: the app must not import the scoring library. The hand-in
  checker flagged `streamlit_app.py` because a docstring mentioned it by name,
  even though nothing was imported - reworded.
- The real risk in this entry is not any of the bugs above. It is the
  explanation I accepted for the negative fusion result, which I later found
  was wrong. That is written up in full below.

## What I changed and why
I stopped looking for evidence that supported the explanation and asked for a
test that could separate it from the alternatives instead. The lead-lag test
in log_05 came out of that, and it is what showed the reading in this entry to
be wrong.

## The negative result - my reading
At this stage I concluded that the fusion failed because headline sentiment
works as a contrarian indicator: the correlation between lagged sector
sentiment and the return it can be traded on is negative in eight of ten
sectors (Energy -0.071, Industrials -0.039; only Consumer and Materials
positive).

That explanation was wrong, and the way it was wrong is the thing worth
recording. It did not contradict a single number I had. The eight negative
sectors supported it, the losing tilt supported it, and reversing the tilt
made money, which supported it again. Every piece of evidence I held pointed
the same way.

What I had not done was compare it against anything. A negative correlation is
equally consistent with a reversal, with news that is already in the price,
and with noise, and the one statistic I was looking at - the lagged
correlation - cannot tell those three apart. I was accumulating confirmation
rather than testing a hypothesis, and confirmation is available for a wrong
answer as readily as for a right one.

The test that settled it looked at the same sentiment against the sector
return on the day before, the same day, and the next day, because the three
explanations leave different fingerprints across those three points.
Same-day correlation is +0.089 and significant in seven of ten sectors;
next-day is -0.013 and significant in one. A reversal would need a
significant negative NEXT-day coefficient and there is not one. The news is
real information that the market has already absorbed by the close, and the
negative signs I had built a story on are mostly noise around zero.

The lesson I take from it is that an explanation which fits all the evidence
is not thereby correct - it has to be the one that survives when a test is
built to distinguish it from its rivals. I should design that test before I
am satisfied with an explanation, not after.
