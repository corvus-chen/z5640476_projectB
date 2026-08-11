"""The look-ahead test I care about most: truncation invariance.

If the backtest ever peeks at future data, then cutting the sample short
would change the results BEFORE the cut. So: run the backtest on the full
panel, run it again on the panel truncated part-way through, and require the
overlapping fund returns and rebalance weights to match exactly.

    python tests/test_no_lookahead.py
"""
import sys
import pathlib

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import etl, features, portfolios, sentiment, fusion  # noqa: E402

CUT = pd.Timestamp("2022-06-30")


_PANEL: pd.DataFrame | None = None


def _panel() -> pd.DataFrame:
    """Load the combined panel once, whether run under pytest or directly.

    The functions below take no arguments on purpose: a `panel` parameter
    would be read as a pytest fixture and the tests would error out.
    """
    global _PANEL
    if _PANEL is None:
        _PANEL = features.combined_returns_panel(
            etl.load_clean_equities(), etl.load_clean_crypto()
        )
    return _PANEL


def test_truncation_invariance() -> None:
    panel = _panel()
    for method in portfolios.METHODS:
        full = portfolios.oos_backtest(panel, method=method)
        cut = portfolios.oos_backtest(panel[panel.index <= CUT], method=method)

        r_full = full["returns"][full["returns"].index <= CUT]
        r_cut = cut["returns"]
        assert r_full.index.equals(r_cut.index), f"{method}: date index differs"
        assert np.allclose(r_full.to_numpy(), r_cut.to_numpy()), \
            f"{method}: fund returns before {CUT.date()} change when the sample is cut"

        w_full = full["weights"][full["weights"].index <= CUT]
        w_cut = cut["weights"]
        assert np.allclose(w_full.to_numpy(), w_cut.to_numpy()), \
            f"{method}: rebalance weights before {CUT.date()} change when the sample is cut"
        print(f"  {method:14s} OK ({len(r_cut)} days, {len(w_cut)} rebalances)")


def test_estimation_window_is_strictly_past() -> None:
    """The first live date must sit after a full estimation window."""
    panel = _panel()
    res = portfolios.oos_backtest(panel, method="min_variance")
    first_live = res["first_live_date"]
    n_before = int((panel.index < first_live).sum())
    assert n_before >= res["window"], "first live date starts inside the estimation window"
    assert res["returns"].index.min() == first_live
    print(f"  first live date {first_live.date()} has {n_before} prior trading days "
          f"(window {res['window']})")


def test_adaptive_tilt_is_truncation_invariant() -> None:
    """The extension learns its tilt direction from data - prove it only looks back.

    The adaptive tilt re-estimates the sentiment/return relationship at every
    rebalance. If that estimate ever reached past the rebalance date, cutting
    the sample would change the earlier weights. It must not.
    """
    equities = etl.load_clean_equities()
    news = etl.load_clean_news()
    days = equities["date"].drop_duplicates()
    ticker_sector = equities.drop_duplicates("ticker").set_index("ticker")["sector"]
    panel = features.returns_panel(equities)

    aligned = features.assemble_headline_panel(news, days)
    index = sentiment.sector_sentiment_index(
        sentiment.ticker_day_sentiment(sentiment.score_headlines(aligned)), days)
    sector_rets = fusion.sector_return_panel(panel, ticker_sector)

    def run(data: pd.DataFrame, sent: pd.DataFrame, rets: pd.DataFrame):
        tilt = fusion.make_adaptive_sentiment_tilt(sent, ticker_sector, rets)
        return portfolios.oos_backtest(data, method="min_variance",
                                       window=252, tilt_fn=tilt)

    full = run(panel, index, sector_rets)
    cut = run(panel[panel.index <= CUT],
              index[index["date"] <= CUT],
              sector_rets[sector_rets.index <= CUT])

    r_full = full["returns"][full["returns"].index <= CUT]
    assert r_full.index.equals(cut["returns"].index)
    assert np.allclose(r_full.to_numpy(), cut["returns"].to_numpy()), \
        "adaptive tilt: fund returns change when the sample is cut - look-ahead"
    w_full = full["weights"][full["weights"].index <= CUT]
    assert np.allclose(w_full.to_numpy(), cut["weights"].to_numpy()), \
        "adaptive tilt: rebalance weights change when the sample is cut - look-ahead"
    print(f"  adaptive tilt  OK ({len(cut['returns'])} days, "
          f"{len(cut['weights'])} rebalances)")


if __name__ == "__main__":
    p = _panel()
    print(f"panel {p.shape[0]} days x {p.shape[1]} assets")
    test_estimation_window_is_strictly_past()
    test_truncation_invariance()
    test_adaptive_tilt_is_truncation_invariant()
    print("no-look-ahead tests passed")
