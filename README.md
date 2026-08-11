# Spotlight - Part B: Funds, Sentiment & App (z5640476)

Part B of the FINS5545 project (DFF Stations 3-4). Spotlight is a systematic
multi-asset investment app: it offers twelve funds built from the Part A data
foundation, each backtested out-of-sample, plus a standalone news-sentiment
index across the ten equity sectors. This folder is also the GitHub repository
that Streamlit deploys; the app entrypoint is `streamlit_app.py` at the root.

## How to run

    pip install -r requirements.txt -r requirements-dev.txt   # dev adds VADER
    python scripts/run_part_b.py            # rebuilds every artifact (~25 s)
    streamlit run streamlit_app.py          # runs the app locally
    python -m pytest tests/                 # smoke + no-look-ahead tests
    python scripts/check_handin.py          # pre-submission check

One script reproduces everything end-to-end. On first run it downloads the
course data ZIP through `src/data_access.py` and the VADER lexicon, both of
which need a network connection once. No raw data is written to disk or
committed; the deployed app reads only the precomputed CSVs under `results/`.

## The funds

Twelve funds - three asset families (Equity, Crypto, Combined) times four
optimisation methods (equal-weight, minimum-variance, maximum-Sharpe, risk
parity). Each (family, method) pair is one fund with its own fact sheet.

Backtest design: walk-forward, monthly rebalancing on the first trading day of
each month, weights estimated on a rolling one-year window of returns strictly
before each rebalance. The first live date is 4 January 2021 for the equity and
combined funds (1 January 2021 for crypto, which trades every day). Risk-free
rate is zero, transaction costs are zero, and both are stated in the report.
Equity and combined funds annualise on 252 days, crypto-only funds on 365.

## What was built

- `src/etl.py` - the Part A cleaning rules re-applied as guards (sample cap,
  ticker-date uniqueness, news dedup on ticker+date+title, UTC normalisation).
- `src/features.py` - daily returns per panel, the combined panel with crypto
  left-joined onto the equity calendar, and headline alignment to the same or
  next trading day.
- `src/portfolios.py` - the four optimisers and the walk-forward out-of-sample
  backtest engine, plus the performance metrics and the fund line-up.
- `src/sentiment.py` - VADER scoring of the raw headlines, ticker-day
  aggregation, and the equal-weight sector index with its one-day lag.
- `src/fusion.py` - the sector sentiment tilt, its before-vs-after comparison,
  and the signal diagnostics that explain the result.
- `src/figures.py` / `src/figstyle.py` - the project design system, shared by
  the report figures and the app theme.
- `streamlit_app.py` - the investor journey: compare funds, read a fact sheet,
  build an allocation, and read the sentiment analytics.

## Innovation extensions

Two extensions, both evaluated against the base fund rather than assumed to
help, and both reported gross and net of a 10 bp turnover cost:

1. **A finance lexicon for VADER** (`src/finance_lexicon.py`). Only 1,831 of
   the 33,033 distinct headline tokens carry a VADER score, and 49.6% of
   headlines score neutral. 46 terms were selected by frequency from the
   headlines themselves - `beat` (2,083 uses), `downgrade`, `plunge` - with a
   written rationale each, and ambiguous terms (`cut`, `hike`, `buy`) excluded
   with reasons. The neutral share falls to 43.4% and 16.1% of headlines are
   rescored.
2. **A tilt that learns its own direction** (`make_adaptive_sentiment_tilt`).
   The naive tilt toward high-sentiment sectors loses to the base fund, and
   the diagnostics say why: the correlation between the lagged sentiment index
   and the return it can be traded on is negative in eight of ten sectors.
   Rather than hard-code the reverse, the adaptive tilt re-estimates that
   correlation at each rebalance from the prior year only and leans whichever
   way the window says. It lifts the Maximum-Sharpe fund from 0.586 to 0.673
   (0.565 to 0.650 after costs) and is covered by the truncation test.

The two do not stack: the lexicon helps the fixed tilt but hurts the adaptive
one, because part of the contrarian edge came from VADER's blind spots.
`results/tables/extension_comparison.csv` holds all ten variants.

3. **A discovery/holdout check on the ranking itself.** Comparing variants
   over one period and keeping the best is a choice fitted to that period, so
   the winner is re-picked on 2021-2022 alone and reported on 2023, which
   played no part in the choice. The adaptive tilt is what tuning selects for
   both funds and it also ranks first on the holdout, but the margin over the
   base fund is small (+0.04 and +0.07 of a Sharpe point), and every
   Minimum-Variance variant decayed into 2023 including the base - a regime
   effect, not a property of the tilt. See
   `results/tables/discovery_holdout.csv`.

Alongside the sector index, `src/sentiment.py` builds a market-wide **fear and
greed gauge**: sentiment averaged across all 50 stocks, rescaled to 0-100 and
standardised. The raw level sits above neutral on 99% of days, so only the
standardised series exposes the fear episodes - the deepest are March 2020 and
early December 2021.

## Outputs

App-readable data (committed, the app reads these):

- `results/data/fund_returns.csv` - daily out-of-sample returns per fund
- `results/data/fund_weights.csv` - target weights at every rebalance
- `results/data/sector_sentiment_index.csv` - daily sector index, raw,
  smoothed, and lagged
- `results/data/fusion_fund_returns.csv` - the sentiment-tilted fund returns

Report tables in `results/tables/` (`performance_metrics.csv`,
`fusion_before_after.csv`, `sentiment_signal_diagnostics.csv`,
`sentiment_coverage.csv`) and figures in `results/figures/`.

## Verification

`tests/test_no_lookahead.py` is the test the backtest rests on: it runs each
fund on the full sample and again on a sample truncated at 30 June 2022, and
requires the overlapping returns and weights to match exactly. A backtest that
peeked at future data would fail it.

## Deploy + hand in

This folder is its own GitHub repository, independent of fins-agent. See
`docs/STUDENT_DEPLOY.md` and PROJECT_BRIEF.md Appendix D:

    python scripts/check_handin.py
    # git init here, commit (results/ included), push to a NEW private repo

Then connect the repo on share.streamlit.io with entrypoint
`streamlit_app.py`. At hand-in, make the repo PUBLIC, submit the live URL and
the repo link, and upload the zipped folder to Moodle.
