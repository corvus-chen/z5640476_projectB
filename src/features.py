"""Station 2 (carried over from Part A) - return panels and text assembly.

Rules applied here:

- Returns are computed within each panel's own calendar FIRST; only then are
  crypto returns left-merged onto the equity trading calendar. Price levels
  are never merged across calendars.
- Equities and the combined fund annualise with 252, crypto-only with 365.
- The text panel keeps raw headline text untouched; scoring it is the
  Station 3 model in src/sentiment.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EQUITY_DAYS_PER_YEAR = 252
CRYPTO_DAYS_PER_YEAR = 365


def daily_returns(prices: pd.DataFrame, price_col: str = "adjClose") -> pd.DataFrame:
    """Simple daily returns per ticker from adjClose, long format.

    Returns are computed within each ticker's own calendar - never across a
    merge - so the first observation per ticker is dropped. Output columns:
    ticker, date, ret.
    """
    df = prices.sort_values(["ticker", "date"]).copy()
    df["ret"] = df.groupby("ticker")[price_col].pct_change()
    return df.loc[df["ret"].notna(), ["ticker", "date", "ret"]].reset_index(drop=True)


def returns_panel(prices: pd.DataFrame) -> pd.DataFrame:
    """Wide date x ticker return panel on the panel's own calendar."""
    wide = daily_returns(prices).pivot(index="date", columns="ticker", values="ret")
    wide.columns.name = None
    return wide


def combined_returns_panel(equities: pd.DataFrame, crypto: pd.DataFrame) -> pd.DataFrame:
    """Wide date x asset return panel on the EQUITY trading calendar.

    Each panel's returns are computed on its own calendar first; the crypto
    returns are then left-joined onto the equity dates, which intentionally
    drops weekend-only crypto moves (a fund trading on equity days could not
    act on them).
    """
    eq_wide = returns_panel(equities)
    cr_wide = returns_panel(crypto)
    return eq_wide.join(cr_wide.reindex(eq_wide.index), how="left")


def assemble_headline_panel(headlines: pd.DataFrame,
                            trading_days: pd.Series) -> pd.DataFrame:
    """Align every headline to its equity trading day, keeping raw titles.

    A headline on a trading day maps to that day; otherwise to the NEXT
    trading day. Headlines dated after the last trading day in the sample
    have no in-sample trading day and are dropped (6 rows here, dated after
    the last 2023 equity trading day).
    """
    days = pd.DatetimeIndex(pd.Series(trading_days).sort_values().unique())
    df = headlines.copy()
    idx = days.searchsorted(df["date"], side="left")
    overflow = idx == len(days)
    df["trading_day"] = days[np.where(overflow, 0, idx)]
    return df[~overflow].reset_index(drop=True)
