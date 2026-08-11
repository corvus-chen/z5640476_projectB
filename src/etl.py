"""Station 1 (carried over from Part A) - load and clean the three datasets.

Part A documented the integrity findings in full; here the same cleaning rules
are applied as guards so the Part B pipeline fails loudly if the hosted data
ever changes. Rules:

- Cap every sample at 2023-12-31 (crypto has 10 stray 2024-01-01 rows).
- Prices must be unique by ticker-date; news is deduplicated on
  ticker + date + title only, because many rows per ticker-date is normal.
- News dates are timezone-aware UTC; convert to tz-naive normalised dates
  before any merge with the tz-naive price dates.
- Raw headline text is kept untouched - VADER needs casing, punctuation, and
  stopwords.
"""
from __future__ import annotations

import pandas as pd

from src import data_access

SAMPLE_START = pd.Timestamp("2020-01-01")
SAMPLE_END = pd.Timestamp("2023-12-31")


def load_clean_equities() -> pd.DataFrame:
    """Equity prices, capped at the sample end, unique by ticker-date."""
    raw = data_access.load_equity_prices()
    df = (raw[raw["date"] <= SAMPLE_END]
          .sort_values(["ticker", "date"]).reset_index(drop=True))
    if df.duplicated(["ticker", "date"]).any():
        raise ValueError("equity prices: duplicate ticker-date rows")
    # Part A found a balanced panel: every ticker covers the pooled calendar.
    per_ticker = df.groupby("ticker")["date"].nunique()
    if per_ticker.nunique() != 1:
        raise ValueError("equity prices: panel is no longer balanced")
    return df


def load_clean_crypto() -> pd.DataFrame:
    """Crypto prices with the stray 2024-01-01 rows dropped (365-day calendar)."""
    raw = data_access.load_crypto_prices()
    df = (raw[raw["date"] <= SAMPLE_END]
          .sort_values(["ticker", "date"]).reset_index(drop=True))
    if df.duplicated(["ticker", "date"]).any():
        raise ValueError("crypto prices: duplicate ticker-date rows")
    return df


def load_clean_news() -> pd.DataFrame:
    """Headlines with tz-naive day-level dates, deduplicated, raw titles kept.

    Deduplication is on ticker + date + title only; the copies usually differ
    just in url (syndicated reprints), so the first row of each group is kept.
    """
    raw = data_access.load_news_headlines()
    df = raw.copy()
    df["date"] = (df["date"].dt.tz_convert("UTC")
                  .dt.tz_localize(None).dt.normalize())
    df = df[df["date"] <= SAMPLE_END]
    df = df[~df.duplicated(["ticker", "date", "title"])]
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)
