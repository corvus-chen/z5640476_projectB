"""Station 3 (extension) - fuse the sentiment index into the equity funds.

The fusion rule is a cross-sectional sector tilt applied at each rebalance:

    w_tilted(i) = w_base(i) * (1 + strength * z(sector of i))

where z is the cross-sectional z-score of the lagged sector sentiment index
across the ten sectors on the rebalance date, clipped to +/- `z_clip` so one
extreme sector cannot dominate. Negative weights are clipped to zero and the
result is renormalised to sum to one, so the fund stays long-only and fully
invested. `strength` controls how far the tilt can move a holding: at
strength = 0.3 and a clipped z of 2, a name's weight moves by at most 60%
of its base value.

Look-ahead safety: the tilt reads `sentiment_lagged`, which is the sector
index already shifted one trading day, so a rebalance on date t uses headline
information from t-1 and earlier. The tilt never touches the covariance
estimate, so any difference in the results comes only from the tilt.

Sentiment applies to equities only - crypto carries no news - so in the
combined fund the crypto sleeve keeps its base weights and only the equity
sleeve is tilted.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_sentiment_tilt(sector_index: pd.DataFrame,
                        ticker_sector: pd.Series,
                        strength: float = 0.3,
                        z_clip: float = 2.0):
    """Build the `tilt_fn(weights, date)` used by portfolios.oos_backtest.

    `sector_index` is the output of sentiment.sector_sentiment_index and must
    carry the `sentiment_lagged` column. `ticker_sector` maps ticker -> sector
    for the equity names; assets missing from it (the crypto sleeve) are left
    untilted.
    """
    lagged = (sector_index.pivot(index="date", columns="sector",
                                 values="sentiment_lagged").sort_index())

    def tilt_fn(weights: pd.Series, date: pd.Timestamp) -> pd.Series:
        if date not in lagged.index:
            return weights
        row = lagged.loc[date].dropna()
        if len(row) < 2 or row.std(ddof=0) == 0:
            return weights
        z = ((row - row.mean()) / row.std(ddof=0)).clip(-z_clip, z_clip)

        sectors = weights.index.map(ticker_sector)
        factor = pd.Series(
            [1.0 + strength * z.get(s, 0.0) if isinstance(s, str) else 1.0
             for s in sectors],
            index=weights.index,
        )
        tilted = (weights * factor).clip(lower=0.0)
        total = tilted.sum()
        return weights if total <= 0 else tilted / total

    return tilt_fn


def sector_return_panel(equity_returns: pd.DataFrame,
                        ticker_sector: pd.Series) -> pd.DataFrame:
    """Equal-weight daily return of each sector, on the equity calendar."""
    return equity_returns.T.groupby(ticker_sector).mean().T


def make_adaptive_sentiment_tilt(sector_index: pd.DataFrame,
                                 ticker_sector: pd.Series,
                                 sector_returns: pd.DataFrame,
                                 strength: float = 0.3,
                                 z_clip: float = 2.0,
                                 lookback: int = 252,
                                 min_obs: int = 120):
    """Sentiment tilt whose DIRECTION is learned walk-forward. (Extension.)

    The fixed tilt in `make_sentiment_tilt` assumes high sentiment predicts
    high returns. The signal diagnostics reject that assumption: eight of ten
    sectors show a negative correlation between the lagged sentiment index and
    the return it is usable for, so buying the loudest-praised sector leans the
    wrong way.

    Flipping the sign by hand would be fitting the whole sample. Instead, at
    each rebalance date t this tilt re-estimates the relationship using ONLY
    the `lookback` trading days before t: it pools the per-sector correlations
    between lagged sentiment and the sector return over that window and takes
    the sign of the pooled mean. If the window says sentiment has led returns
    positively, the fund tilts toward high-sentiment sectors; if it says the
    opposite, it tilts away. Until `min_obs` observations are available, the
    tilt stays neutral and the fund holds its base weights.

    The estimate uses only past data, so the truncation-invariance test still
    holds. `signs_` records the direction chosen at each rebalance for the
    report.
    """
    lagged = (sector_index.pivot(index="date", columns="sector",
                                 values="sentiment_lagged").sort_index())
    shared = [c for c in lagged.columns if c in sector_returns.columns]
    lagged = lagged[shared]
    rets = sector_returns[shared].sort_index()
    signs: dict[pd.Timestamp, dict] = {}

    def _direction(date: pd.Timestamp) -> float:
        past_s = lagged[lagged.index < date].tail(lookback)
        past_r = rets[rets.index < date].tail(lookback)
        common = past_s.index.intersection(past_r.index)
        if len(common) < min_obs:
            return 0.0
        corrs = [past_s.loc[common, c].corr(past_r.loc[common, c])
                 for c in shared]
        pooled = float(np.nanmean(corrs))
        signs[date] = {"pooled_corr": pooled, "n_obs": len(common)}
        return float(np.sign(pooled))

    def tilt_fn(weights: pd.Series, date: pd.Timestamp) -> pd.Series:
        if date not in lagged.index:
            return weights
        direction = _direction(date)
        if direction == 0.0:
            return weights
        row = lagged.loc[date].dropna()
        if len(row) < 2 or row.std(ddof=0) == 0:
            return weights
        z = ((row - row.mean()) / row.std(ddof=0)).clip(-z_clip, z_clip)

        sectors = weights.index.map(ticker_sector)
        factor = pd.Series(
            [1.0 + direction * strength * z.get(s, 0.0)
             if isinstance(s, str) else 1.0 for s in sectors],
            index=weights.index,
        )
        tilted = (weights * factor).clip(lower=0.0)
        total = tilted.sum()
        return weights if total <= 0 else tilted / total

    tilt_fn.signs_ = signs
    return tilt_fn


def sign_history(tilt_fn) -> pd.DataFrame:
    """The direction the adaptive tilt chose at each rebalance, for the report."""
    rows = [{"date": d, **v} for d, v in sorted(tilt_fn.signs_.items())]
    out = pd.DataFrame(rows)
    if not out.empty:
        out["direction"] = np.sign(out["pooled_corr"]).astype(int)
    return out


def lead_lag_diagnostics(sector_index: pd.DataFrame,
                         equity_returns: pd.DataFrame,
                         ticker_sector: pd.Series) -> pd.DataFrame:
    """Does sentiment lead prices, move with them, or follow them?

    `signal_diagnostics` shows the tilt leans the wrong way, but a negative
    correlation is consistent with three different stories - reversal,
    news already in the price, or noise - and they need separating.

    Correlating the RAW sector sentiment on day t against the sector return on
    t-1, t and t+1 does that, with a p-value for each:

    - a large, significant SAME-day correlation with nothing at t+1 says the
      news and the price move together and there is nothing left to trade;
    - a significant t+1 correlation would mean genuine predictive content;
    - a significant t-1 correlation would mean the coverage follows the move.
    """
    from scipy import stats

    sector_ret = sector_return_panel(equity_returns, ticker_sector)
    raw = sector_index.pivot(index="date", columns="sector", values="sentiment")
    rows = []
    for sector in sector_ret.columns:
        if sector not in raw.columns:
            continue
        pair = pd.concat([raw[sector].rename("sent"),
                          sector_ret[sector].rename("ret")], axis=1).dropna()
        out = {"sector": sector, "n_days": len(pair)}
        for label, series in [("same_day", pair["ret"]),
                              ("next_day", pair["ret"].shift(-1)),
                              ("prev_day", pair["ret"].shift(1))]:
            d = pd.concat([pair["sent"], series.rename("r")], axis=1).dropna()
            corr, p = stats.pearsonr(d["sent"], d["r"])
            out[f"corr_{label}"] = corr
            out[f"p_{label}"] = p
        rows.append(out)
    return pd.DataFrame(rows).sort_values("corr_same_day", ascending=False)


def horizon_diagnostics(sector_index: pd.DataFrame,
                        equity_returns: pd.DataFrame,
                        ticker_sector: pd.Series,
                        horizons=(1, 5, 21)) -> pd.DataFrame:
    """Is there predictive signal at a lower frequency than daily?

    The daily test says headline sentiment is absorbed by the close. That does
    not rule out a slower effect, so sentiment averaged over the past k
    trading days is tested against the return over the NEXT k trading days.

    Two design choices keep the answer honest:

    - Observations are sampled every k days, not every day. Overlapping
      windows share data and would inflate significance badly at k = 21.
    - Each horizon is run twice. The ABSOLUTE test uses raw sector returns and
      is dominated by the market factor common to all ten sectors. The
      CROSS-SECTIONAL test subtracts the day's mean across sectors from both
      sentiment and returns, which is what the tilt actually bets on: it moves
      weight between sectors and takes no view on the market.

    Returns one row per horizon and variant, pooled across sectors, with the
    number of independent observations behind each estimate.
    """
    from scipy import stats

    sector_ret = sector_return_panel(equity_returns, ticker_sector)
    raw = sector_index.pivot(index="date", columns="sector", values="sentiment")
    shared = [c for c in raw.columns if c in sector_ret.columns]
    # Align the dates BEFORE anything is sampled by position. The return panel
    # starts a day after the sentiment index, because the first return is lost
    # to the differencing, and `iloc[::k]` on two differently-indexed frames
    # would then step through different calendars.
    common = raw.index.intersection(sector_ret.index).sort_values()
    raw = raw.loc[common, shared]
    sector_ret = sector_ret.loc[common, shared]

    rows = []
    for k in horizons:
        # Past-k-day mean sentiment, and the compounded next-k-day return.
        sent_k = raw.rolling(k, min_periods=max(1, k // 2)).mean()
        fwd_k = ((1 + sector_ret).rolling(k).apply(np.prod, raw=True) - 1).shift(-k)

        for variant in ("absolute", "cross-sectional"):
            s, r = sent_k.copy(), fwd_k.copy()
            if variant == "cross-sectional":
                s = s.sub(s.mean(axis=1), axis=0)
                r = r.sub(r.mean(axis=1), axis=0)
            # Non-overlapping: step k days so no two observations share data.
            s, r = s.iloc[::k], r.iloc[::k]
            pair = pd.concat([s.stack().rename("sent"),
                              r.stack().rename("ret")], axis=1).dropna()
            if len(pair) < 30:
                continue
            corr, p = stats.pearsonr(pair["sent"], pair["ret"])
            rows.append({
                "horizon_days": k,
                "variant": variant,
                "n_obs": len(pair),
                "n_periods": int(len(s.dropna(how="all"))),
                "correlation": corr,
                "p_value": p,
                "significant_5pct": bool(p < 0.05),
            })
    out = pd.DataFrame(rows)
    # Several horizons and two variants are searched at once, so a single
    # p-value below 0.05 is roughly what chance delivers. Carry the corrected
    # threshold in the table rather than leaving the reader to apply it.
    if not out.empty:
        out["bonferroni_threshold"] = 0.05 / len(out)
        out["significant_corrected"] = out["p_value"] < out["bonferroni_threshold"]
    return out


def bootstrap_sharpe_difference(base: pd.Series, variant: pd.Series,
                                days_per_year: int = 252,
                                n_boot: int = 5000,
                                block: int = 21,
                                seed: int = 42) -> dict:
    """Is a Sharpe improvement bigger than sampling noise?

    A point estimate on its own says nothing about whether a variant beats its
    base, and with three years of daily data the noise is large. This resamples
    the two return series TOGETHER with a stationary bootstrap, so the pairing
    and the autocorrelation survive, and reports a confidence interval for the
    difference in Sharpe ratios.

    An interval that spans zero means the improvement is not established,
    however attractive the point estimate looks.
    """
    rng = np.random.default_rng(seed)
    joined = pd.concat([base.rename("base"), variant.rename("variant")],
                       axis=1).dropna()
    a = joined["variant"].to_numpy()
    b = joined["base"].to_numpy()
    n = len(a)

    def sharpe(x: np.ndarray) -> float:
        sd = x.std()
        return float(x.mean() / sd * np.sqrt(days_per_year)) if sd > 0 else np.nan

    observed = sharpe(a) - sharpe(b)
    p_switch = 1.0 / block
    draws = np.empty(n_boot)
    for k in range(n_boot):
        idx = np.empty(n, dtype=int)
        i = rng.integers(n)
        for j in range(n):
            idx[j] = i
            i = rng.integers(n) if rng.random() < p_switch else (i + 1) % n
        draws[k] = sharpe(a[idx]) - sharpe(b[idx])

    lo, hi = np.percentile(draws, [2.5, 97.5])
    p_value = 2 * min((draws <= 0).mean(), (draws >= 0).mean())
    return {
        "sharpe_base": sharpe(b),
        "sharpe_variant": sharpe(a),
        "difference": observed,
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_value": float(p_value),
        "significant_5pct": bool(p_value < 0.05),
        "n_days": n,
        "n_boot": n_boot,
    }


def discovery_holdout(variants: dict[str, pd.Series],
                      split: str = "2023-01-01",
                      days_per_year: int = 252,
                      baseline: str | None = None) -> pd.DataFrame:
    """Split the out-of-sample record into a tuning window and a holdout.

    Comparing five variants on the same period and keeping the winner is
    itself a choice fitted to that period. This applies the harder test: pick
    the best variant on the DISCOVERY window only (2021-2022), then report how
    that pick did on data it was never compared over (2023).

    Returns one row per variant with the Sharpe ratio in each window, flagging
    which variant tuning would have selected. A variant that wins the
    discovery window and then collapses in the holdout has been fitted, not
    found - and reporting that is the point of the exercise.
    """
    from src.portfolios import performance_metrics

    cut = pd.Timestamp(split)
    rows = []
    for name, r in variants.items():
        r = r.dropna()
        disc, hold = r[r.index < cut], r[r.index >= cut]
        if len(disc) < 60 or len(hold) < 60:
            continue
        rows.append({
            "variant": name,
            "discovery_sharpe": performance_metrics(disc, days_per_year)["sharpe"],
            "discovery_return": performance_metrics(disc, days_per_year)["ann_return"],
            "holdout_sharpe": performance_metrics(hold, days_per_year)["sharpe"],
            "holdout_return": performance_metrics(hold, days_per_year)["ann_return"],
            "n_discovery_days": len(disc),
            "n_holdout_days": len(hold),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out

    pick = out.loc[out["discovery_sharpe"].idxmax(), "variant"]
    out["selected_by_tuning"] = out["variant"] == pick
    out["sharpe_decay"] = out["holdout_sharpe"] - out["discovery_sharpe"]
    if baseline is not None and baseline in out["variant"].values:
        base_hold = out.loc[out["variant"] == baseline, "holdout_sharpe"].iloc[0]
        out["holdout_vs_baseline"] = out["holdout_sharpe"] - base_hold
    return out.sort_values("discovery_sharpe", ascending=False)


def apply_costs(daily_returns: pd.Series, weights: pd.DataFrame,
                cost_bps: float = 10.0,
                drifted: pd.DataFrame | None = None) -> pd.Series:
    """Charge a one-way transaction cost on turnover at each rebalance.

    `cost_bps` is charged on the one-way turnover of each rebalance, booked on
    the rebalance date, and turnover is measured from the drifted holdings the
    fund actually had. Zero-cost results stay the headline (the brief allows
    it, stated); this is the robustness layer, because a tilt that only wins
    before costs has not really won.
    """
    turnover = turnover_series(weights, drifted)
    charge = (turnover * cost_bps / 1e4).reindex(daily_returns.index).fillna(0.0)
    return daily_returns - charge


def compare_before_after(base: dict, tilted: dict, days_per_year: int,
                         label: str) -> pd.DataFrame:
    """The required before-vs-after table for one base/tilted fund pair."""
    from src.portfolios import performance_metrics

    rows = []
    for name, res in [(f"{label} (base)", base), (f"{label} + sentiment", tilted)]:
        m = performance_metrics(res["returns"], days_per_year)
        rows.append({
            "fund": name,
            "ann_return": m["ann_return"],
            "ann_vol": m["ann_vol"],
            "sharpe": m["sharpe"],
            "max_drawdown": m["max_drawdown"],
            "growth_of_1": float((1.0 + res["returns"]).prod()),
        })
    out = pd.DataFrame(rows)
    diff = out.iloc[1, 1:] - out.iloc[0, 1:]
    diff_row = {"fund": "difference"}
    diff_row.update(diff.to_dict())
    out = pd.concat([out, pd.DataFrame([diff_row])], ignore_index=True)
    base_to = average_turnover(base["weights"], base.get("drifted_weights"))
    tilt_to = average_turnover(tilted["weights"], tilted.get("drifted_weights"))
    out["avg_turnover"] = [base_to, tilt_to, tilt_to - base_to]
    return out


def turnover_series(weights: pd.DataFrame,
                    drifted: pd.DataFrame | None = None) -> pd.Series:
    """One-way turnover at each rebalance: 0.5 * sum |w_target - w_held|.

    The fund does not trade from its previous TARGET, it trades from whatever
    those positions drifted to over the holding period. Comparing consecutive
    targets would count drift the fund never had to trade, so `drifted` (the
    weights on the eve of each rebalance) is the correct baseline. Falling
    back to consecutive targets keeps older artifacts readable.
    """
    if len(weights) < 2:
        return pd.Series(dtype=float)
    if drifted is None:
        change = weights.diff().iloc[1:]
    else:
        prior = drifted.shift(1).reindex(weights.index)
        change = (weights - prior).iloc[1:]
    return 0.5 * change.abs().sum(axis=1)


def average_turnover(weights: pd.DataFrame,
                     drifted: pd.DataFrame | None = None) -> float:
    """Mean one-way turnover across rebalances."""
    series = turnover_series(weights, drifted)
    return float(series.mean()) if len(series) else float("nan")


def signal_diagnostics(sector_index: pd.DataFrame,
                       equity_returns: pd.DataFrame,
                       ticker_sector: pd.Series) -> pd.DataFrame:
    """Does the lagged sector index predict next-day sector returns at all?

    Reports, per sector, the correlation between the lagged sentiment index
    and the equal-weight sector return on the same trading day (the return the
    signal is actually usable for). This is the honest test of whether the
    fusion has anything to work with, reported whatever the answer.
    """
    sector_ret = (equity_returns.T.groupby(ticker_sector).mean().T)
    lagged = sector_index.pivot(index="date", columns="sector",
                                values="sentiment_lagged")
    rows = []
    for sector in sector_ret.columns:
        if sector not in lagged.columns:
            continue
        pair = pd.concat([lagged[sector].rename("sent"),
                          sector_ret[sector].rename("ret")], axis=1).dropna()
        rows.append({
            "sector": sector,
            "n_days": len(pair),
            "corr_lagged_sentiment_vs_return": pair["sent"].corr(pair["ret"]),
            "mean_return_high_sentiment": pair.loc[
                pair["sent"] > pair["sent"].median(), "ret"].mean(),
            "mean_return_low_sentiment": pair.loc[
                pair["sent"] <= pair["sent"].median(), "ret"].mean(),
        })
    out = pd.DataFrame(rows)
    out["spread_bps_per_day"] = 1e4 * (out["mean_return_high_sentiment"]
                                       - out["mean_return_low_sentiment"])
    return out.sort_values("corr_lagged_sentiment_vs_return", ascending=False)


def apply_sentiment(weights: pd.Series, sector_index: pd.DataFrame,
                    ticker_sector: pd.Series, date: pd.Timestamp,
                    strength: float = 0.3) -> pd.Series:
    """One-shot tilt of a single weight vector (used by the app's fact sheet)."""
    return make_sentiment_tilt(sector_index, ticker_sector, strength)(weights, date)
