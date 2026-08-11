"""Station 3 - the sentiment model: score headlines into a sector index.

Design choices, all defended in the report:

- Text handling: headlines are scored RAW. VADER reads casing (all-caps is an
  intensifier), punctuation ("!"), degree modifiers, and negation, so
  stripping or lower-casing would destroy signal the model is built on.
- Aggregation: mean compound score across a ticker's headlines on a trading
  day, then an equal-weight mean across the tickers in a sector. Equal
  weighting keeps a single heavily-covered name (AAPL prints far more
  headlines than SHW) from becoming the sector index.
- No-headline ticker-days are DROPPED from the sector average rather than
  treated as neutral. Scoring a silent day as 0.0 would pull the index toward
  zero on quiet days and confuse "no news" with "balanced news"; Part A also
  found genuine multi-month collection blackouts for some tickers, which a
  zero-fill would turn into fake neutral sentiment. The daily coverage count
  is carried alongside the index so thin days are visible.
- Look-ahead: headlines are aligned to the same or next trading day, then the
  index is lagged by one further trading day. A Saturday or Monday headline,
  both aligned to Monday, is first usable for Tuesday's trade.
"""
from __future__ import annotations

import os
import zipfile

import pandas as pd

NEUTRAL_BAND = 0.05  # VADER's own convention for "neutral" compound scores


def _analyzer():
    """VADER, downloading the lexicon on first use (a build step, never the app)."""
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        # nltk downloads over urllib with the system CA store, which fails on
        # some macOS Python installs; point it at certifi's bundle instead.
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        nltk.download("vader_lexicon", quiet=True)
    return SentimentIntensityAnalyzer()


def score_headlines(aligned: pd.DataFrame,
                    extra_lexicon: dict[str, float] | None = None) -> pd.DataFrame:
    """Score every aligned headline with VADER, keeping the raw text intact.

    `aligned` is the Station 2 headline panel (ticker, sector, date, title,
    trading_day). `extra_lexicon` optionally adds finance terms to VADER's
    vocabulary - the innovation extension - and is applied before scoring.

    Returns the input columns plus `compound` and a `is_neutral` flag.
    """
    sia = _analyzer()
    if extra_lexicon:
        sia.lexicon.update(extra_lexicon)
    df = aligned.copy()
    df["compound"] = [sia.polarity_scores(t or "")["compound"] for t in df["title"]]
    df["is_neutral"] = df["compound"].abs() < NEUTRAL_BAND
    return df


def ticker_day_sentiment(scored: pd.DataFrame) -> pd.DataFrame:
    """Mean compound score per ticker per trading day, with headline counts."""
    return (scored.groupby(["ticker", "sector", "trading_day"])
            .agg(sentiment=("compound", "mean"),
                 n_headlines=("compound", "size"),
                 n_neutral=("is_neutral", "sum"))
            .reset_index()
            .rename(columns={"trading_day": "date"})
            .sort_values(["ticker", "date"])
            .reset_index(drop=True))


def sector_sentiment_index(ticker_day: pd.DataFrame,
                           trading_days: pd.Series,
                           lag_days: int = 1,
                           smooth_days: int = 5) -> pd.DataFrame:
    """Daily equal-weight sector sentiment index, lagged to be usable at t.

    Columns: date, sector, sentiment (equal-weight mean across the tickers
    that printed a headline), n_tickers, n_headlines, sentiment_smoothed
    (`smooth_days` rolling mean), and sentiment_lagged - the index shifted
    forward by `lag_days` trading days, which is the ONLY column any trading
    rule may read on date t.
    """
    days = pd.DatetimeIndex(pd.Series(trading_days).sort_values().unique())
    raw = (ticker_day.groupby(["sector", "date"])
           .agg(sentiment=("sentiment", "mean"),
                n_tickers=("ticker", "nunique"),
                n_headlines=("n_headlines", "sum"))
           .reset_index())

    frames = []
    for sector, grp in raw.groupby("sector"):
        s = grp.set_index("date").reindex(days)
        s["sector"] = sector
        s["sentiment_smoothed"] = (s["sentiment"]
                                   .rolling(smooth_days, min_periods=1).mean())
        # Lag AFTER smoothing so the smoothed value on date t still uses only
        # information available before t.
        s["sentiment_lagged"] = s["sentiment_smoothed"].shift(lag_days)
        frames.append(s.rename_axis("date").reset_index())

    out = pd.concat(frames, ignore_index=True)
    out["n_tickers"] = out["n_tickers"].fillna(0).astype(int)
    out["n_headlines"] = out["n_headlines"].fillna(0).astype(int)
    cols = ["date", "sector", "sentiment", "sentiment_smoothed",
            "sentiment_lagged", "n_tickers", "n_headlines"]
    return out[cols].sort_values(["sector", "date"]).reset_index(drop=True)


def fear_greed_index(ticker_day: pd.DataFrame,
                     trading_days: pd.Series,
                     smooth_days: int = 5,
                     lag_days: int = 1) -> pd.DataFrame:
    """Market-wide fear and greed gauge from the same ticker-day scores.

    Built in three steps, following the Week 10 construction:

    1. Average the daily sentiment across all 50 stocks, equal-weighted, to a
       single market series.
    2. Rescale the compound score from its -1/+1 range onto 0-100, where 50 is
       neutral. This is the number a user reads on the gauge.
    3. Standardise it (subtract the full-sample mean, divide by the standard
       deviation). The rescaled LEVEL sits above neutral on almost every day,
       because headline sentiment carries a positive baseline, so the raw
       gauge would read "greedy" permanently and say nothing. The standardised
       series is what exposes the fear spikes.

    `fear_greed_lagged` is the shifted standardised series, the only column a
    trading rule may read on date t.
    """
    days = pd.DatetimeIndex(pd.Series(trading_days).sort_values().unique())
    market = (ticker_day.groupby("date")
              .agg(sentiment=("sentiment", "mean"),
                   n_tickers=("ticker", "nunique"),
                   n_headlines=("n_headlines", "sum"))
              .reindex(days).rename_axis("date"))

    market["fear_greed_raw"] = 50.0 * (market["sentiment"] + 1.0)
    smoothed = market["fear_greed_raw"].rolling(smooth_days, min_periods=1).mean()
    market["fear_greed_smoothed"] = smoothed
    market["fear_greed_z"] = (smoothed - smoothed.mean()) / smoothed.std()
    market["fear_greed_lagged"] = market["fear_greed_z"].shift(lag_days)
    market["n_tickers"] = market["n_tickers"].fillna(0).astype(int)
    market["n_headlines"] = market["n_headlines"].fillna(0).astype(int)
    return market.reset_index()


def fear_greed_extremes(index: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """The deepest fear and highest greed days, for the report and the app."""
    df = index.dropna(subset=["fear_greed_z"])
    cols = ["date", "fear_greed_raw", "fear_greed_smoothed", "fear_greed_z",
            "n_headlines"]
    low = df.nsmallest(n, "fear_greed_z")[cols].assign(extreme="fear")
    high = df.nlargest(n, "fear_greed_z")[cols].assign(extreme="greed")
    return pd.concat([low, high], ignore_index=True)


def coverage_summary(ticker_day: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    """Validation table for the index: coverage and the neutral-score share.

    The neutral share is the headline diagnostic the brief warns about - plain
    VADER calls about half of finance headlines neutral, and many are false
    neutrals, which is what the lexicon extension is meant to reduce.
    """
    by_sector = (scored.groupby("sector")
                 .agg(n_headlines=("compound", "size"),
                      n_tickers=("ticker", "nunique"),
                      mean_compound=("compound", "mean"),
                      neutral_share=("is_neutral", "mean"))
                 .reset_index())
    cov = (ticker_day.groupby("sector")["date"].nunique()
           .rename("n_days_with_news").reset_index())
    return by_sector.merge(cov, on="sector").sort_values("sector")


def load_finance_lexicon(path: str) -> dict[str, float]:
    """Read a finance-term lexicon (term, score) CSV for the VADER extension."""
    df = pd.read_csv(path)
    return dict(zip(df["term"].str.lower(), df["score"].astype(float)))
