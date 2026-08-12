"""Station 3 - funds: optimal portfolios + walk-forward out-of-sample backtest.

Backtest design (stated assumptions):

- Walk-forward, no look-ahead: weights at each rebalance are estimated on a
  rolling window of returns strictly BEFORE the rebalance date, and applied
  from that date until the next rebalance.
- Rebalance on the first trading day of each month. The out-of-sample period
  starts at the first rebalance date with a full estimation window behind it,
  not on the first date in the data.
- Weights DRIFT with prices between rebalances, as a real fund's do. Holding
  the targets fixed on every day in between would assume daily rebalancing and
  pay the fund a rebalancing bonus it never earned.
- Transaction costs are zero in the headline results and charged separately in
  the robustness layer. Risk-free rate = 0 for the Sharpe ratio.
- The covariance can optionally be Ledoit-Wolf shrunk (`shrink=True`), which
  the estimation study uses to test how much of the equity result is sample
  noise in the covariance matrix.
- Long-only, fully invested: 0 <= w <= 1, sum(w) = 1.
- Mean and covariance are annualised BEFORE optimisation. Daily-return
  covariances are ~1e-4 and make solver objectives smaller than the default
  tolerance, so SLSQP can return the starting point unchanged; annualising
  rescales the objective so the solver actually moves.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

METHODS = ("equal_weight", "min_variance", "max_sharpe", "risk_parity")
RISK_FREE_RATE = 0.0
DEFAULT_WINDOW = 252  # trading days in the rolling estimation window


def _solve(objective, n: int) -> np.ndarray:
    w0 = np.full(n, 1.0 / n)
    res = minimize(
        objective, w0, method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    if not res.success:
        raise RuntimeError(f"optimiser failed: {res.message}")
    w = np.clip(res.x, 0.0, None)
    return w / w.sum()


def _covariance(window_returns: pd.DataFrame, shrink: bool) -> np.ndarray:
    """Sample covariance, or the Ledoit-Wolf shrinkage estimate.

    The sample covariance of 50 assets from 252 days is estimated from fewer
    observations per parameter than the problem really needs, and its extreme
    eigenvalues are the ones the optimiser leans on hardest. Ledoit and Wolf
    shrink it toward a scaled identity by an intensity chosen to minimise
    expected squared error, which pulls those extremes back.

    This is the standard remedy for the sample-noise diagnosis in Section 2,
    so it belongs in the report as a test of that diagnosis rather than as a
    performance trick.
    """
    if not shrink:
        return window_returns.cov().to_numpy() * 252
    from sklearn.covariance import LedoitWolf
    lw = LedoitWolf().fit(window_returns.to_numpy())
    return lw.covariance_ * 252


def optimise_weights(window_returns: pd.DataFrame, method: str,
                     shrink: bool = False) -> pd.Series:
    """Target weights from one estimation window of daily returns.

    The window holds daily returns; mean and covariance are scaled by 252
    before optimising. The scaling leaves the optimum unchanged for all three
    objectives (variance and the risk-parity gap scale by a constant, and the
    Sharpe ratio is scale-invariant), but it lifts the objective above SLSQP's
    tolerance so the solver moves off its equal-weight starting point.
    """
    n = window_returns.shape[1]
    if method == "equal_weight":
        w = np.full(n, 1.0 / n)
        return pd.Series(w, index=window_returns.columns)

    mu = window_returns.mean().to_numpy() * 252
    cov = _covariance(window_returns, shrink)

    if method == "min_variance":
        w = _solve(lambda w: w @ cov @ w, n)
    elif method == "max_sharpe":
        def neg_sharpe(w):
            vol = np.sqrt(w @ cov @ w)
            return -(w @ mu - RISK_FREE_RATE) / vol if vol > 0 else 0.0
        w = _solve(neg_sharpe, n)
    elif method == "risk_parity":
        def rp_gap(w):
            port_var = w @ cov @ w
            rc = w * (cov @ w) / port_var
            return ((rc - 1.0 / n) ** 2).sum()
        w = _solve(rp_gap, n)
    else:
        raise ValueError(f"unknown method: {method}")
    return pd.Series(w, index=window_returns.columns)


# Rebalance schedules. Calendar-period options trade on the first trading day
# of each period; "21d" is the fixed-interval alternative the brief mentions.
REBALANCE_RULES = {
    "weekly": "W",
    "fortnightly": None,      # every second weekly date
    "monthly": "M",
    "quarterly": "Q",
    "21d": None,              # every 21 trading days
}


def rebalance_dates(dates: pd.DatetimeIndex, window: int,
                    frequency: str = "monthly") -> pd.DatetimeIndex:
    """Rebalance dates for a schedule, skipping the initial estimation window.

    Calendar schedules fire on the first trading day of each period, so a
    holiday never silently drops a rebalance.
    """
    eligible = np.arange(len(dates)) >= window
    if frequency == "21d":
        return dates[eligible & (np.arange(len(dates)) % 21 == 0)]
    if frequency not in REBALANCE_RULES:
        raise ValueError(f"unknown rebalance frequency: {frequency}")

    freq = REBALANCE_RULES["weekly" if frequency == "fortnightly" else frequency]
    periods = dates.to_period(freq)
    first_of_period = np.r_[True, periods[1:] != periods[:-1]]
    hits = dates[first_of_period & eligible]
    return hits[::2] if frequency == "fortnightly" else hits


def oos_backtest(returns: pd.DataFrame, method: str = "min_variance",
                 window: int = DEFAULT_WINDOW, tilt_fn=None,
                 frequency: str = "monthly", shrink: bool = False) -> dict:
    """Walk-forward out-of-sample backtest of one (panel, method) fund.

    Weights are set at each rebalance and then DRIFT with prices until the
    next one, which is how a real fund behaves. Holding the target weights
    fixed on every day in between would quietly assume the fund trades back to
    target daily - the opposite of rebalancing monthly, and it would flatter
    the result by harvesting a free rebalancing bonus the fund never earned.

    Drift is computed exactly rather than iteratively: within a holding
    period the value of $1 is V_t = sum_i w_i * prod_{s<=t}(1 + r_is), and the
    fund's daily return is the change in V.

    Returns the daily out-of-sample returns, the target weights at each
    rebalance, the drifted weights just before each rebalance (what the fund
    actually held, so turnover is measured against reality), and growth of $1.

    `tilt_fn(weights, date) -> weights` optionally post-processes the target
    weights at each rebalance - this is how the sentiment fusion enters, so
    the tilted fund runs through exactly the same engine as its base fund.
    It is the tilt function's own job to use only information available
    before `date`.
    """
    panel = returns.sort_index()
    dates = panel.index
    rebals = rebalance_dates(dates, window, frequency)
    if len(rebals) == 0:
        raise ValueError("not enough history for one estimation window")

    weights, drifted, daily = {}, {}, []
    for i, t in enumerate(rebals):
        pos = dates.get_loc(t)
        est = panel.iloc[pos - window:pos]
        w = optimise_weights(est, method, shrink=shrink)
        if tilt_fn is not None:
            w = tilt_fn(w, t)
        weights[t] = w

        end = dates.get_loc(rebals[i + 1]) if i + 1 < len(rebals) else len(dates)
        held = panel.iloc[pos:end].fillna(0.0)
        gross = (1.0 + held).cumprod()          # each asset's growth of $1
        value = gross @ w                       # portfolio value, from $1
        period = value / value.shift(1)
        period.iloc[0] = value.iloc[0]          # first day starts from $1
        daily.append(period - 1.0)

        # What the fund is actually holding on the eve of the next rebalance.
        end_weights = w * gross.iloc[-1]
        drifted[t] = end_weights / end_weights.sum()

    fund = pd.concat(daily)
    fund.name = method
    return {
        "returns": fund,
        "weights": pd.DataFrame(weights).T.rename_axis("date"),
        "drifted_weights": pd.DataFrame(drifted).T.rename_axis("date"),
        "growth": (1.0 + fund).cumprod(),
        "first_live_date": rebals[0],
        "window": window,
        "frequency": frequency,
        "shrink": shrink,
        "n_rebalances": len(rebals),
    }


def performance_metrics(daily_returns: pd.Series,
                        periods_per_year: int = 252) -> dict:
    """Annualised return (geometric), volatility, Sharpe (rf=0), max drawdown.

    Both annualised means are reported. The headline `ann_return` is geometric
    (what an investor's dollar actually compounds to), while the Sharpe ratio
    uses the arithmetic mean, as the ratio is conventionally defined. The two
    diverge by the volatility drag, which is large for the crypto funds: at
    ~80% annualised volatility a fund can post a positive arithmetic mean and
    still lose money geometrically.
    """
    r = daily_returns.dropna()
    growth = (1.0 + r).cumprod()
    n_years = len(r) / periods_per_year
    ann_vol = r.std() * np.sqrt(periods_per_year)
    return {
        "ann_return": growth.iloc[-1] ** (1.0 / n_years) - 1.0,
        "ann_return_arithmetic": r.mean() * periods_per_year,
        "ann_vol": ann_vol,
        "sharpe": (r.mean() * periods_per_year - RISK_FREE_RATE) / ann_vol,
        "max_drawdown": (growth / growth.cummax() - 1.0).min(),
        "n_days": len(r),
        "first_date": r.index[0].date(),
        "last_date": r.index[-1].date(),
    }


def drawdown_series(daily_returns: pd.Series) -> pd.Series:
    """Drawdown from the running peak of growth of $1, for the drawdown figure."""
    growth = (1.0 + daily_returns.dropna()).cumprod()
    return growth / growth.cummax() - 1.0


# --- the fund line-up -------------------------------------------------------
# One fund per (asset family, method) pair, because that is what an investor
# buys and what a fact sheet covers. Each family keeps its own calendar: the
# crypto-only fund trades and annualises on 365 days, the equity-only and
# combined funds on 252. The estimation window is one year of that family's
# own observations.

FAMILY_DAYS_PER_YEAR = {"Equity": 252, "Crypto": 365, "Combined": 252}

METHOD_LABELS = {
    "equal_weight": "Equal-Weight",
    "min_variance": "Minimum-Variance",
    "max_sharpe": "Maximum-Sharpe",
    "risk_parity": "Risk Parity",
}


def fund_name(family: str, method: str) -> str:
    return f"{family} {METHOD_LABELS[method]}"


def build_funds(panels: dict[str, pd.DataFrame],
                methods=METHODS) -> dict[str, dict]:
    """Backtest every (family, method) fund and key the results by fund name."""
    funds = {}
    for family, panel in panels.items():
        days = FAMILY_DAYS_PER_YEAR[family]
        for method in methods:
            res = oos_backtest(panel, method=method, window=days)
            res["family"] = family
            res["method"] = method
            res["days_per_year"] = days
            res["metrics"] = performance_metrics(res["returns"], days)
            funds[fund_name(family, method)] = res
    return funds


def rebalance_frequency_study(panel: pd.DataFrame, methods=METHODS,
                              frequencies=("weekly", "fortnightly", "monthly",
                                           "quarterly"),
                              window: int = DEFAULT_WINDOW,
                              days_per_year: int = 252,
                              cost_bps: float = 10.0) -> pd.DataFrame:
    """How often should the fund trade? Same fund, four schedules.

    Trading more often tracks the optimiser's latest view more closely but
    pays for it in turnover, so the comparison is only honest net of costs.
    Reported both ways, with the turnover that drives the difference.
    """
    from src.fusion import average_turnover, apply_costs

    rows = []
    for method in methods:
        for freq in frequencies:
            res = oos_backtest(panel, method=method, window=window,
                               frequency=freq)
            gross = performance_metrics(res["returns"], days_per_year)
            net = performance_metrics(
                apply_costs(res["returns"], res["weights"], cost_bps,
                            res["drifted_weights"]), days_per_year)
            rows.append({
                "method": METHOD_LABELS[method],
                "frequency": freq,
                "n_rebalances": res["n_rebalances"],
                "sharpe": gross["sharpe"],
                "ann_return": gross["ann_return"],
                "ann_vol": gross["ann_vol"],
                "max_drawdown": gross["max_drawdown"],
                "sharpe_net_costs": net["sharpe"],
                "ann_return_net_costs": net["ann_return"],
                "avg_turnover": average_turnover(res["weights"],
                                                 res["drifted_weights"]),
                "annual_turnover": average_turnover(
                    res["weights"], res["drifted_weights"]
                ) * res["n_rebalances"] / (len(res["returns"]) / days_per_year),
            })
    return pd.DataFrame(rows)


def window_study(panels: dict[str, pd.DataFrame],
                 methods=("min_variance", "max_sharpe", "risk_parity"),
                 min_window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Rolling against expanding estimation windows.

    Section 2 argues the estimation sample is too thin, which invites the
    obvious question: why not simply use a longer one? An expanding window is
    the cheapest way to answer it, and the answer is not the same for every
    universe. More history means less estimation noise but a longer memory of
    a regime that may have ended, and the two effects pull in opposite
    directions depending on how stable the assets are.
    """
    rows = []
    for family, panel in panels.items():
        days = FAMILY_DAYS_PER_YEAR[family]
        dates = panel.index
        rebals = rebalance_dates(dates, days, "monthly")
        for method in methods:
            rolling = oos_backtest(panel, method=method, window=days)
            # Same engine, but the estimation slice starts at the first
            # observation instead of `days` back.
            daily = []
            for i, t in enumerate(rebals):
                pos = dates.get_loc(t)
                w = optimise_weights(panel.iloc[:pos], method)
                end = (dates.get_loc(rebals[i + 1]) if i + 1 < len(rebals)
                       else len(dates))
                held = panel.iloc[pos:end].fillna(0.0)
                value = (1.0 + held).cumprod() @ w
                period = value / value.shift(1)
                period.iloc[0] = value.iloc[0]
                daily.append(period - 1.0)
            expanding = pd.concat(daily)

            r = performance_metrics(rolling["returns"], days)["sharpe"]
            e = performance_metrics(expanding, days)["sharpe"]
            rows.append({"family": family, "method": METHOD_LABELS[method],
                         "sharpe_rolling": r, "sharpe_expanding": e,
                         "change": e - r})
    return pd.DataFrame(rows)


def shrinkage_study(panels: dict[str, pd.DataFrame],
                    methods=("min_variance", "max_sharpe", "risk_parity"),
                    window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Test the sample-noise diagnosis by fixing the noise it points at.

    Section 2 argues that the equity ordering comes from estimating 50 means
    and a 50-by-50 covariance on 252 days. Ledoit-Wolf shrinkage is the
    standard correction for the covariance half of that problem, so running
    each fund with and without it tests the diagnosis rather than assuming it.

    The test discriminates, because the three methods use the covariance
    differently: minimum variance is a pure function of it, risk parity needs
    only its diagonal, and maximum Sharpe is dominated by the expected returns
    that shrinkage does not touch.
    """
    rows = []
    for family, panel in panels.items():
        days = FAMILY_DAYS_PER_YEAR[family]
        for method in methods:
            for shrink in (False, True):
                res = oos_backtest(panel, method=method, window=days,
                                   shrink=shrink)
                met = performance_metrics(res["returns"], days)
                rows.append({
                    "family": family,
                    "method": METHOD_LABELS[method],
                    "shrinkage": shrink,
                    "sharpe": met["sharpe"],
                    "ann_return": met["ann_return"],
                    "ann_vol": met["ann_vol"],
                    "max_drawdown": met["max_drawdown"],
                    "n_assets_held": int((res["weights"].iloc[-1] > 0.005).sum()),
                })
    out = pd.DataFrame(rows)
    wide = out.pivot_table(index=["family", "method"], columns="shrinkage",
                           values="sharpe").reset_index()
    wide.columns = ["family", "method", "sharpe_sample", "sharpe_shrunk"]
    wide["change"] = wide["sharpe_shrunk"] - wide["sharpe_sample"]
    return out.merge(wide[["family", "method", "change"]],
                     on=["family", "method"])


def metrics_table(funds: dict[str, dict]) -> pd.DataFrame:
    """The required performance-metrics table across funds and methods."""
    rows = []
    for name, res in funds.items():
        m = res["metrics"]
        rows.append({
            "fund": name,
            "family": res["family"],
            "method": METHOD_LABELS[res["method"]],
            "ann_return": m["ann_return"],
            "ann_return_arithmetic": m["ann_return_arithmetic"],
            "ann_vol": m["ann_vol"],
            "sharpe": m["sharpe"],
            "max_drawdown": m["max_drawdown"],
            "growth_of_1": float((1.0 + res["returns"]).prod()),
            "n_assets_held": int((res["weights"].iloc[-1] > 0.005).sum()),
            "days_per_year": res["days_per_year"],
            "first_live_date": m["first_date"],
            "last_date": m["last_date"],
            "n_days": m["n_days"],
        })
    return pd.DataFrame(rows).sort_values(["family", "sharpe"],
                                          ascending=[True, False])
