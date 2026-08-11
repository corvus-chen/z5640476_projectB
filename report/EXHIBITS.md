# Exhibit map (planning aid, like OUTLINE.md - not a deliverable)

One row per required Part B exhibit (PROJECT_BRIEF.md, Section 5), the file
that satisfies it, and the headline numbers to quote when interpreting it.
Regenerate everything with `python scripts/run_part_b.py` (about 90 seconds).

Every number below was read from the generated artifact, not recalled. If a
figure is rebuilt, re-read the table rather than trusting this file.

## Required exhibits

| # | Brief requirement | Exhibit file(s) | Key numbers for the text |
|---|-------------------|-----------------|--------------------------|
| 1 | Performance-metrics table across funds and methods | `results/tables/performance_metrics.csv` | 12 funds = 3 families x 4 methods. Best per family: Combined Maximum-Sharpe S=0.98 (+24.0% p.a., -25.8% DD); Crypto Risk Parity S=0.86 (+44.3%, -79.9%); Equity Equal-Weight S=0.82 (+12.6%, -20.2%). Worst: Crypto Maximum-Sharpe S=0.07 (-23.5% p.a., -88.9% DD). $1 grows to between $0.45 and $3.00 |
| 2 | Growth-of-$1 figure comparing the methods | `results/figures/growth_of_1_combined.png` | Combined family, four methods, live 04 Jan 2021 to 29 Dec 2023 (753 trading days) |
| 3 | Drawdown figure for at least one fund | `results/figures/drawdown_combined_max_sharpe.png` | Combined Maximum-Sharpe, deepest drawdown -25.8% |
| 4 | Portfolio-weights-over-time across methods | `results/figures/weights_combined_across_methods.png` (single-fund version: `weights_combined_min_variance.png`) | Same universe/dates under three objectives. Minimum-Variance concentrates in Healthcare (rises ~25% -> ~50%) and holds almost no crypto; Maximum-Sharpe swings violently with a wide crypto band; Risk Parity is near-static |
| 5 | Sharpe / return-vs-risk barplot across funds and methods | `results/figures/sharpe_by_fund.png` | All 12 funds, grouped by family, rf = 0 |
| 6 | Sentiment-index time series for the equity sectors | `results/figures/sector_sentiment_index.png` | 10 sectors, 146,830 scored headlines, 21-day rolling mean. Every sector mean is positive: Utilities highest (+0.179), Financials lowest (+0.090) |
| 7 | Fusion before-vs-after, table AND figure | `results/tables/fusion_before_after.csv`, `results/figures/fusion_min_variance.png`, `fusion_max_sharpe.png` | Min-Variance Sharpe 0.479 -> 0.457; Max-Sharpe 0.573 -> 0.509. Both WORSE. Turnover rises 0.151 -> 0.215 and 0.331 -> 0.365 |

## Required data files (the app reads these)

`results/data/fund_returns.csv`, `fund_weights.csv`,
`sector_sentiment_index.csv`, and `results/tables/performance_metrics.csv`.

## Extension exhibits (Innovation, 30%)

| Extension | Exhibit file(s) | Key numbers for the text |
|---|---|---|
| Finance lexicon | `results/figures/lexicon_effect.png`, `results/tables/finance_lexicon.csv`, `lexicon_effect.csv` | Only 1,831 of 33,033 distinct headline tokens carry a VADER score. 46 terms added; neutral share 49.6% -> 43.4%; 16.1% of headlines rescored; sd of the compound score 0.288 -> 0.317 |
| Adaptive-direction tilt | `results/figures/extension_comparison.png`, `results/tables/extension_comparison.csv` | Max-Sharpe: base 0.573, fixed tilt 0.509, ADAPTIVE 0.658 (net of 10bp: 0.552 / 0.487 / 0.636). Min-Variance: 0.479 / 0.457 / 0.512. Direction estimated as -1 at all 36 rebalances, pooled correlation -0.047 to -0.002 |
| Why the naive tilt fails | `results/tables/sentiment_signal_diagnostics.csv` | Lagged sentiment vs the return it can be traded on: negative in 8 of 10 sectors, mean -0.0205. Energy most negative (-0.071, -31.8 bp/day); Consumer most positive (+0.028) |
| The two extensions conflict | `sentiment_signal_diagnostics_extended.csv` vs the plain version | Extended lexicon weakens the contrarian signal: mean correlation -0.0205 -> -0.0156, negative sectors 8/10 -> 7/10. Adaptive tilt therefore FALLS from 0.658 to 0.540 on Max-Sharpe |
| Discovery / holdout | `results/figures/discovery_holdout.png`, `results/tables/discovery_holdout.csv` | Tuning on 2021-22 selects adaptive/plain for BOTH funds; it also ranks first on 2023 (Max-Sharpe 0.835 vs base 0.765; Min-Var 0.101 vs base 0.060). All Min-Variance variants decay ~0.58 into 2023, base included |
| Rebalance frequency | `results/figures/rebalance_frequency.png`, `results/tables/rebalance_frequency.csv` | Quarterly worst for every method. Best net: Equal-Weight and Risk Parity fortnightly, Maximum-Sharpe monthly, Minimum-Variance weekly. Annual turnover 0.27 (EW quarterly) to 7.67 (MS weekly) |
| Fear and greed index | `results/figures/fear_greed_index.png`, `results/data/fear_greed_index.csv`, `results/tables/fear_greed_extremes.csv` | Raw gauge above neutral on 99.0% of days. Deepest standardised troughs 18/20/19 Mar 2020 (z = -3.64, -3.19, -3.14) and 02 Dec 2021 |
| Design system | `src/figstyle.py`, `tools/check_palette.py` | 12 categorical slots, worst-case pairwise deltaE 16.9 across normal, deuteranopic and protanopic vision - identical to the 5-slot brand palette, because brand blue vs violet is still the binding pair |

## Backtest design to state explicitly in the report

- Walk-forward, rolling 252-day estimation window (NOT expanding - the Week 10
  reference implementation uses expanding; state the choice).
- Rebalance on the first trading day of each month; 36 rebalances.
- First live date 04 Jan 2021 (equity and combined), 01 Jan 2021 (crypto).
- Long-only, fully invested: 0 <= w <= 1, sum w = 1.
- Risk-free rate = 0. Headline results are gross of costs; the 10 bp
  robustness layer is reported alongside.
- Weights DRIFT between rebalances (buy-and-hold within a holding period).
- Annualisation 252 for equity and combined, 365 for crypto-only.
- Sentiment lagged one trading day after alignment; the tilt z-score is
  cross-sectional across the ten sectors (the reference implementation
  standardises per stock over a rolling window - state the difference).

## Notes for the write-up (facts only - interpretation is mine to write)

- Equity Equal-Weight (S=0.82) beats every optimised equity fund I built.
  DeMiguel, Garlappi and Uppal (2009) is the citation for that result.
- Crypto Maximum-Sharpe reports a POSITIVE Sharpe (0.065) and a NEGATIVE
  annualised return (-23.5%). Not a bug: at 79.8% annualised volatility the
  arithmetic mean (+5.2%) and the geometric mean diverge. Report both.
- The fusion result is negative and stays negative. The brief and the Week 10
  lecture both say an explained negative result earns full marks.
- Reading the best of five variants off one out-of-sample period is itself a
  selection; that is what the discovery/holdout table is for, and the holdout
  margin over the base fund is small (+0.04 and +0.07 of a Sharpe point).
- The Week 10 lecture's own numbers differ from mine (e.g. its combined risk
  parity 0.78 against my 0.89) because it uses an expanding window. Do not
  quote its figures as if they were mine.
