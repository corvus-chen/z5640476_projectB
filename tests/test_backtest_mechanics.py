"""The backtest's accounting, checked against cases with a known answer.

Weights drift with prices between rebalances. Holding them fixed instead
would silently mean trading back to target every single day, which harvests a
rebalancing bonus the fund never earned - it lifted the Combined
Maximum-Sharpe Sharpe ratio from 0.98 to 1.03 before this was fixed. These
tests pin the arithmetic down.

    python -m pytest tests/test_backtest_mechanics.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import etl, features, portfolios  # noqa: E402

_PANEL = None


def _panel() -> pd.DataFrame:
    global _PANEL
    if _PANEL is None:
        _PANEL = features.combined_returns_panel(
            etl.load_clean_equities(), etl.load_clean_crypto())
    return _PANEL


def test_single_asset_reproduces_the_asset():
    """A fund holding one asset at 100% must return exactly that asset."""
    panel = _panel()
    col = panel.columns[0]
    one = panel[[col]].dropna()
    res = portfolios.oos_backtest(one, method="equal_weight")
    truth = one.loc[res["returns"].index, col]
    assert np.allclose(res["returns"].to_numpy(), truth.to_numpy(), atol=1e-12), \
        "single-asset fund does not reproduce its only holding"


def test_buy_and_hold_between_rebalances():
    """Within one holding period the fund is buy-and-hold, not constant-weight.

    Growth over the period must equal the weighted average of the assets'
    growth (sum w_i * prod(1+r_i)), which is strictly what drifting means.
    """
    panel = _panel().iloc[:, :5].dropna()
    res = portfolios.oos_backtest(panel, method="equal_weight",
                                  frequency="quarterly")
    w0 = res["weights"].iloc[0]
    start, nxt = res["weights"].index[0], res["weights"].index[1]
    seg = panel.loc[(panel.index >= start) & (panel.index < nxt)]
    expected = float(((1 + seg).prod() * w0).sum())
    actual = float((1 + res["returns"].loc[seg.index]).prod())
    assert abs(expected - actual) < 1e-10, \
        f"period growth {actual} is not buy-and-hold ({expected})"


def test_drifted_weights_are_a_valid_portfolio():
    res = portfolios.oos_backtest(_panel(), method="min_variance")
    drifted = res["drifted_weights"]
    assert np.allclose(drifted.sum(axis=1), 1.0), "drifted weights do not sum to 1"
    assert (drifted >= -1e-12).all().all(), "drifted weights went negative"
    assert float((drifted - res["weights"]).abs().max().max()) > 1e-3, \
        "weights never drift - the backtest is still constant-weight"


def test_targets_are_long_only_and_fully_invested():
    for method in portfolios.METHODS:
        w = portfolios.oos_backtest(_panel(), method=method)["weights"]
        assert np.allclose(w.sum(axis=1), 1.0), f"{method}: weights do not sum to 1"
        assert (w >= -1e-9).all().all(), f"{method}: negative weight in a long-only fund"


def test_rebalance_schedules_are_ordered_by_frequency():
    """Weekly must fire more often than monthly, monthly more than quarterly."""
    dates = _panel().index
    counts = {f: len(portfolios.rebalance_dates(dates, 252, f))
              for f in ("weekly", "fortnightly", "monthly", "quarterly")}
    assert counts["weekly"] > counts["fortnightly"] > counts["monthly"] > counts["quarterly"], \
        f"schedule frequencies are not ordered: {counts}"
    for f, n in counts.items():
        assert n > 0, f"{f} produced no rebalance dates"


if __name__ == "__main__":
    test_single_asset_reproduces_the_asset()
    test_buy_and_hold_between_rebalances()
    test_drifted_weights_are_a_valid_portfolio()
    test_targets_are_long_only_and_fully_invested()
    test_rebalance_schedules_are_ordered_by_frequency()
    print("backtest mechanics tests passed")
