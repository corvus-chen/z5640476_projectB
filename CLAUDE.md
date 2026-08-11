# CLAUDE.md - my working instructions for Claude Code (z5640476, Part B)

These are the instructions I give Claude Code when working on this project.
The full assignment brief is `PROJECT_BRIEF.md`; the data reference is
`context/DATA_GUIDE.md`. Read both before touching any data.

## What this project is

Part B (Funds, Sentiment & App, DFF Stations 3-4) of the FINS3645 FinTech
project: build systematically managed funds from the cleaned equity and crypto
data with a walk-forward out-of-sample backtest, score the assembled headlines
into a sector news-sentiment index, fuse the sentiment into the equity funds,
and deliver everything through a deployed Streamlit app plus a written report.
The data foundation (cleaning rules, return panels, headline alignment) is
reused from my own Part A.

## Language

- Everything that lands in this folder is in English: code, comments, report
  text, AI logs, and this file.

## Environment

- Interpreter: `/Users/nuochen/Documents/GitHub/fins-agent/.venv/bin/python`
  (shared repo venv; this folder has no venv of its own).
- App dependencies stay in `requirements.txt` (slim - the deployed app must
  run on Streamlit's free tier). Build-only packages (nltk) go in
  `requirements-dev.txt`. If a new package is needed, add it to the right
  file first, then install into the venv.
- Work only inside this folder. Do not read or reference files outside it -
  the course requires that the assistant only sees my own work. Two
  exceptions: the shared interpreter path above, and my own Part A folder
  (`../z5640476_projectA`), which the brief explicitly lets me reuse.

## Data rules (carried over from my Part A)

- Load all data through `src/data_access.py`. Never commit raw data; only
  derived artifacts under `results/`.
- Use `adjClose` for returns. Cap every sample at 2023-12-31 (crypto has 10
  stray 2024-01-01 rows).
- Deduplicate news on ticker + date + title. Many rows per ticker-date is
  normal, not a duplicate.
- Compute returns within each panel first, then left-merge the crypto returns
  onto the equity trading calendar. Never merge price levels across the two
  calendars and difference afterwards.
- News dates are timezone-aware UTC; price dates are tz-naive. Normalise
  timezone and dtype before any merge.
- Align each headline to its equity trading day: the same day if it is a
  trading day, otherwise the next trading day.
- Keep the raw headline text for VADER - no stopword, casing, or punctuation
  stripping before scoring.
- Annualise equities and the combined fund with 252, crypto-only with 365.

## Part B red lines

- No look-ahead, anywhere. Backtest weights are formed only from data strictly
  before the rebalance date. The out-of-sample period starts after the initial
  estimation window, and the report states the first live date and window
  length.
- Sentiment used in any decision for trading day t must come from day t-1 or
  earlier (lag the index by at least one trading day after alignment).
- The deployed app only reads precomputed CSVs from `results/`. It never
  imports nltk, never runs VADER, and never recomputes a backtest.
- Sentiment applies to equities only - crypto has no news.
- State assumptions explicitly in code and report: risk-free rate = 0 for
  Sharpe, zero transaction costs (unless we add a cost model as an extension).
- Sanity-check optimiser output: weights must actually differ across methods
  (daily-return covariances are tiny and solvers can silently stall).

## Outputs

- Exact required filenames the app and markers read:
  `results/data/fund_returns.csv`, `results/data/fund_weights.csv`,
  `results/data/sector_sentiment_index.csv`,
  `results/tables/performance_metrics.csv`.
- Figures go to `results/figures/`, each self-contained: title/caption,
  labelled axes, units, and sample period.
- `scripts/run_part_b.py` must reproduce every artifact end-to-end from a
  clean checkout. Run order: `run_part_b.py`, then
  `streamlit run streamlit_app.py`, then `scripts/check_handin.py`.

## My rules and skills (`.claude/`)

The rules below are binding. Read them before writing code that touches a
backtest, a signal, or an exhibit:

- `.claude/rules/no-lookahead.md` - the rule I will not accept a violation of,
  and the truncation test that proves compliance.
- `.claude/rules/verify-numbers.md` - never state a statistic from memory;
  every number must be re-runnable.
- `.claude/rules/my-words-not-yours.md` - where the assistant stops and my own
  interpretation begins.

Skills I invoke rather than re-explaining each time:

- `.claude/skills/audit-backtest/` - run before any new number reaches the
  report.
- `.claude/skills/check-exhibit/` - run after generating or changing a figure.
- `.claude/skills/log-session/` - draft the factual half of an `ai/` log entry.

## Verification (see context/verify_ai_output.md)

- Never invent a citation, a statistic, or a source.
- Every number must trace to the data or to a computation I can re-run. Show
  your working for any number you produce.
- Flag any claim you cannot verify instead of stating it confidently.
- Remind me to check your output before I rely on it.

## AI workflow and logging

- After each task, draft a prompt-log entry in `ai/` (`log_NN_<task>.md`):
  the prompts used, what you produced, and issues found. Leave the judgment
  sections ("what was wrong or risky", "what I changed and why") for me to
  dictate - do not write my reflections for me.
- The report's analysis and economic interpretation are mine. You may compute,
  plot, structure, and check style, but do not write interpretive prose for me
  to paste in.

## Planned innovation extensions (to be finalised)

Candidates, in rough priority order - I will decide which to build:

- Extend VADER's lexicon with finance terms (AI-proposed words and scores,
  which I review) and measure the change in neutral-headline share and index
  behaviour.
- Carry my Part A abnormal news-flow (attention) z-score into Part B as a
  weighting or screening signal, with a before-vs-after evaluation.
- A turnover / transaction-cost model on the backtests.
- Extra optimisation methods beyond the required two, and a custom figure
  design system shared by the report and the app.
