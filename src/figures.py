"""Part B exhibits, drawn through the project design system in figstyle.py.

Every figure is self-contained: title, a subtitle carrying units and the
sample period, labelled axes, direct series labels, and a source footer.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import figstyle as fs
from src import portfolios as pf

SOURCE = ("Source: course project data (equity and crypto daily adjusted closes, "
          "news headlines), 2020-2023. Out-of-sample backtest, author's calculations.")


def _period(index: pd.Index) -> str:
    return f"{index.min():%d %b %Y} to {index.max():%d %b %Y}"


def _label_offsets(ax, values, min_gap_pt: float = 11.0) -> list[float]:
    """Vertical offsets (in points) that stop direct labels from colliding.

    Series ending close together - Equal-Weight and Risk Parity finish $0.04
    apart - would otherwise print on top of each other. Labels are pushed
    apart in display space, smallest value first, so the reading order still
    matches the series order.
    """
    ax.figure.canvas.draw()
    px_per_pt = ax.figure.dpi / 72.0
    y_px = ax.transData.transform([(0.0, v) for v in values])[:, 1]
    order = sorted(range(len(values)), key=lambda i: y_px[i])
    offsets = [0.0] * len(values)
    placed = None
    for i in order:
        target = y_px[i]
        if placed is not None and target - placed < min_gap_pt * px_per_pt:
            target = placed + min_gap_pt * px_per_pt
        offsets[i] = (target - y_px[i]) / px_per_pt
        placed = target
    return offsets


def growth_of_one(funds: dict, names: list[str], path: str,
                  title: str = "Growth of $1 across fund methods") -> None:
    """Cumulative return of $1 invested at the first out-of-sample date."""
    series = {n: funds[n]["growth"] for n in names}
    idx = list(series.values())[0].index
    fig, (ax,) = fs.new_figure(
        title,
        f"Value of $1 invested at the first live backtest date, {_period(idx)}. "
        "Weights are re-optimised on the first trading day of each month from "
        "the prior year of returns only.",
        height=3.6,
    )
    for slot, (name, g) in enumerate(series.items()):
        ax.plot(g.index, g.to_numpy(), color=fs.SERIES[slot % len(fs.SERIES)],
                linewidth=1.5)
    ax.set_ylabel("Value of $1 (USD)")
    ax.set_xlabel("Date")
    ax.axhline(1.0, color=fs.BASELINE, linewidth=0.8, zorder=0)
    fs.year_axis(ax)
    ax.margins(x=0.28)

    finals = [g.iloc[-1] for g in series.values()]
    for slot, ((name, g), dy) in enumerate(zip(series.items(),
                                               _label_offsets(ax, finals))):
        fs.direct_label(ax, g.index[-1], g.iloc[-1],
                        f"{name.split(' ', 1)[1]}  ${g.iloc[-1]:.2f}",
                        fs.SERIES[slot % len(fs.SERIES)], dy=dy)
    fs.finish(fig, path, SOURCE)


def drawdown(funds: dict, name: str, path: str) -> None:
    """Drawdown from the running peak for one fund."""
    dd = pf.drawdown_series(funds[name]["returns"])
    trough = dd.idxmin()
    fig, (ax,) = fs.new_figure(
        f"Drawdown: {name}",
        f"Percentage below the running peak of growth of $1, {_period(dd.index)}. "
        f"Deepest drawdown {dd.min():.1%} on {trough:%d %b %Y}.",
        height=3.0,
    )
    ax.fill_between(dd.index, 100 * dd.to_numpy(), 0, color=fs.SERIES[0], alpha=0.25)
    ax.plot(dd.index, 100 * dd.to_numpy(), color=fs.SERIES[0], linewidth=1.2)
    ax.scatter([trough], [100 * dd.min()], s=18, color=fs.INK, zorder=5)
    fs.direct_label(ax, trough, 100 * dd.min(), f"  {dd.min():.1%}", fs.INK, dy=-8)
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Date")
    fs.year_axis(ax)
    fs.finish(fig, path, SOURCE)


def _sector_bands(grouped: pd.DataFrame):
    """Order sector weights largest-first and colour every band distinctly.

    All ten sectors get their own slot from the extended palette, which is
    validated pair-by-pair under normal and colour-blind vision by
    tools/check_palette.py, so no two bands share a hue. Crypto is pulled out
    and stacked last in the design system's dark ink, because it is an asset
    class rather than a sector and the reader should be able to find it
    instantly.
    """
    has_crypto = "Crypto" in grouped.columns
    equity = grouped.drop(columns=["Crypto"]) if has_crypto else grouped
    cols = list(equity.mean().sort_values(ascending=False).index)
    colours = fs.series_colours(len(cols))
    out = grouped[cols].copy()
    if has_crypto:
        out["Crypto"] = grouped["Crypto"]
        cols = cols + ["Crypto"]
        colours = list(colours) + [fs.INK_2]
    return out[cols], cols, colours


def weights_over_time_across_methods(funds: dict, family: str, methods: list[str],
                                     path: str,
                                     ticker_sector: pd.Series | None = None) -> None:
    """The required exhibit: weights over time for one family, ACROSS methods.

    Side-by-side panels share the same sector colouring, so the reader can see
    how differently each objective allocates the same investable universe over
    the same dates.
    """
    names = [pf.fund_name(family, m) for m in methods]
    panels = {}
    for n in names:
        w = funds[n]["weights"]
        g = (w.T.groupby(w.columns.map(ticker_sector).fillna("Crypto")).sum().T
             if ticker_sector is not None else w)
        panels[n] = g
    # One colour order shared by every panel, ranked on the first fund.
    ref = panels[names[0]]
    has_crypto = any("Crypto" in g.columns for g in panels.values())
    order = [c for c in ref.mean().sort_values(ascending=False).index
             if c != "Crypto"]
    colours = dict(zip(order, fs.series_colours(len(order))))
    if has_crypto:
        order = order + ["Crypto"]
        colours["Crypto"] = fs.INK_2

    fig, axes = fs.new_figure(
        f"Portfolio weights over time: {family} funds",
        f"Target weights at each monthly rebalance, by sector, {_period(ref.index)}. "
        "Same universe and dates under each objective; crypto is the dark band.",
        n_axes=len(names), height=3.4, sharex=True,
    )
    for i, (ax, n) in enumerate(zip(axes, names)):
        g = panels[n].reindex(columns=order).fillna(0.0)
        ax.stackplot(g.index, *[g[c].to_numpy() * 100 for c in order],
                     colors=[colours[c] for c in order],
                     labels=order, edgecolor="none")
        ax.set_title(pf.METHOD_LABELS[methods[i]], fontsize=8.5,
                     loc="left", color=fs.INK, pad=4)
        ax.set_ylim(0, 100)
        # One shared 0-100 scale and one shared date axis, so only the left
        # panel carries tick labels and only the middle one is titled.
        if i:
            ax.tick_params(labelleft=False)
        if i == len(names) // 2:
            ax.set_xlabel("Rebalance date")
        fs.year_axis(ax, compact=True)
    axes[0].set_ylabel("Weight (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False,
               fontsize=7.5, bbox_to_anchor=(0.5, -0.13))
    fs.finish(fig, path, SOURCE)


def weights_over_time(funds: dict, name: str, path: str,
                      ticker_sector: pd.Series | None = None) -> None:
    """Target weights at each rebalance, stacked as sector bands.

    Individual assets are unreadable across 60 holdings, so weights are
    aggregated to sector, with the coins pooled into a single Crypto band.
    The bands sum to 100% on every rebalance date, so a widening band means
    the fund is holding more of that sector.
    """
    w = funds[name]["weights"]
    if ticker_sector is not None:
        grouped = w.T.groupby(w.columns.map(ticker_sector).fillna("Crypto")).sum().T
    else:
        grouped = w
    grouped, cols, colours = _sector_bands(grouped)

    fig, (ax,) = fs.new_figure(
        f"Portfolio weights over time: {name}",
        f"Target weights set on the first trading day of each month, "
        f"{_period(w.index)}, aggregated to sector and stacked to 100%. "
        "Sectors are ordered by average weight, with crypto stacked last in "
        "dark grey. The weights move each month as the covariance matrix is "
        "re-estimated.",
        height=3.8,
    )
    ax.stackplot(grouped.index, *[grouped[c].to_numpy() * 100 for c in cols],
                 colors=colours, labels=cols, edgecolor="none")
    ax.set_ylabel("Weight (%)")
    ax.set_xlabel("Rebalance date")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper center", ncol=4, frameon=False, fontsize=7.5,
              bbox_to_anchor=(0.5, -0.38))
    fs.year_axis(ax)
    fs.finish(fig, path, SOURCE)


def sharpe_barplot(metrics: pd.DataFrame, path: str) -> None:
    """Sharpe ratio across every (family, method) fund."""
    df = metrics.sort_values(["family", "sharpe"])
    families = list(dict.fromkeys(df["family"]))
    fig, (ax,) = fs.new_figure(
        "Sharpe ratio across funds and methods",
        "Annualised Sharpe ratio (risk-free rate assumed zero) over each fund's "
        "out-of-sample period. Equity and combined funds annualise on 252 days, "
        "crypto-only funds on 365.",
        height=3.6,
    )
    colours = {f: fs.SERIES[i % len(fs.SERIES)] for i, f in enumerate(families)}
    y = np.arange(len(df))
    ax.barh(y, df["sharpe"], color=[colours[f] for f in df["family"]], height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(df["method"], fontsize=8)
    for yi, (v, fam) in enumerate(zip(df["sharpe"], df["family"])):
        ax.text(v + 0.02, yi, f"{v:.2f}", va="center", fontsize=7.5, color=fs.INK_2)
    ax.set_xlabel("Sharpe ratio (annualised, rf = 0)")
    ax.grid(axis="y", visible=False)
    for fam in families:
        rows = np.where(df["family"].to_numpy() == fam)[0]
        ax.text(-0.02, rows.mean(), fam, ha="right", va="center", fontsize=8.5,
                fontweight="bold", color=colours[fam],
                transform=ax.get_yaxis_transform())
    fs.finish(fig, path, SOURCE)


def sentiment_index(index: pd.DataFrame, path: str,
                    sectors: list[str] | None = None, smooth: int = 21) -> None:
    """Sector news-sentiment index over time.

    The daily index is too noisy to read five sectors off at once, so the
    exhibit plots a `smooth`-day (about one trading month) rolling mean. The
    published CSV keeps the daily series.
    """
    wide = index.pivot(index="date", columns="sector", values="sentiment")
    if sectors:
        wide = wide[sectors]
    wide = wide.rolling(smooth, min_periods=max(3, smooth // 3)).mean()
    fig, (ax,) = fs.new_figure(
        "News-sentiment index by equity sector",
        f"Equal-weight mean VADER compound score across the five tickers in each "
        f"sector, {smooth}-day rolling mean, {_period(wide.index)}. Scores run "
        "from -1 (most negative) to +1; ticker-days with no headlines are "
        "excluded. Every sector averages positive - headline sentiment carries "
        "a well-known optimistic bias.",
        height=3.6,
    )
    series = {col: wide[col].dropna() for col in wide.columns}
    for slot, s in enumerate(series.values()):
        ax.plot(s.index, s.to_numpy(), color=fs.SERIES[slot % len(fs.SERIES)],
                linewidth=1.1)
    ax.axhline(0.0, color=fs.BASELINE, linewidth=0.8, zorder=0)
    ax.set_ylabel("Sentiment (VADER compound)")
    ax.set_xlabel("Trading day")
    fs.year_axis(ax)
    ax.margins(x=0.18)

    finals = [s.iloc[-1] for s in series.values()]
    for slot, ((col, s), dy) in enumerate(zip(series.items(),
                                              _label_offsets(ax, finals))):
        fs.direct_label(ax, s.index[-1], s.iloc[-1], f"  {col}",
                        fs.SERIES[slot % len(fs.SERIES)], dy=dy)
    fs.finish(fig, path, SOURCE)


def fear_greed(index: pd.DataFrame, extremes: pd.DataFrame, path: str,
               smooth: int = 21) -> None:
    """The market fear and greed gauge: raw level against the standardised one.

    The daily gauge is too noisy to read the episodes off, so the exhibit
    plots a `smooth`-day rolling mean of both panels. The published CSV keeps
    the daily series.
    """
    df = index.dropna(subset=["fear_greed_z"]).set_index("date")
    df = df[["fear_greed_smoothed", "fear_greed_z"]].rolling(
        smooth, min_periods=max(3, smooth // 3)).mean().dropna()
    fig, axes = fs.new_figure(
        "Fear and greed across the whole equity market",
        "Sentiment averaged over all 50 stocks. On the left the raw 0-100 "
        f"gauge, above neutral on {100 * (index['fear_greed_raw'] > 50).mean():.0f}% "
        "of days because headline sentiment has a positive baseline. On the "
        "right the same series standardised, which is what makes the fear "
        f"episodes visible. Both panels show a {smooth}-day rolling mean.",
        n_axes=2, height=3.2,
    )
    ax_raw, ax_z = axes
    ax_raw.plot(df.index, df["fear_greed_smoothed"], color=fs.SERIES[0],
                linewidth=1.1)
    ax_raw.axhline(50, color=fs.BASELINE, linewidth=0.9, zorder=0)
    ax_raw.set_ylabel("Gauge (0-100, 50 = neutral)")
    ax_raw.set_title("Raw level: always greedy", fontsize=9, loc="left",
                     color=fs.INK)

    ax_z.plot(df.index, df["fear_greed_z"], color=fs.SERIES[0], linewidth=1.0)
    ax_z.fill_between(df.index, df["fear_greed_z"], 0,
                      where=df["fear_greed_z"] < 0, color=fs.SERIES[2],
                      alpha=0.35, interpolate=True)
    ax_z.axhline(0, color=fs.BASELINE, linewidth=0.9, zorder=0)
    ax_z.set_ylabel("Standard deviations from mean")
    ax_z.set_title("Standardised: the fear episodes appear", fontsize=9,
                   loc="left", color=fs.INK)

    # Mark the deepest smoothed trough, which is the episode a reader can see,
    # rather than the single worst day, which the smoothing has averaged away.
    trough = df["fear_greed_z"].idxmin()
    ax_z.scatter([trough], [df["fear_greed_z"].min()], s=20, color=fs.INK,
                 zorder=5)
    fs.direct_label(ax_z, trough, df["fear_greed_z"].min(),
                    f"  {trough:%b %Y}", fs.INK, dy=6)

    for ax in axes:
        ax.set_xlabel("Trading day")
        fs.year_axis(ax)
    fs.finish(fig, path, SOURCE)


def discovery_holdout(holdout: pd.DataFrame, path: str) -> None:
    """Sharpe in the tuning window against the untouched holdout year."""
    funds_shown = list(dict.fromkeys(holdout["fund"]))
    fig, axes = fs.new_figure(
        "What tuning picks, and whether it survives",
        "Each variant's Sharpe ratio over the 2021-2022 discovery window and "
        "over 2023, which was never used to choose between them. The variant "
        "tuning would have selected is marked. A variant that wins on the "
        "left and collapses on the right was fitted, not found.",
        n_axes=len(funds_shown), height=3.6,
    )
    order = list(dict.fromkeys(holdout["variant"]))
    for ax, fund in zip(axes, funds_shown):
        sub = holdout[holdout["fund"] == fund].set_index("variant").loc[
            [v for v in order if v in set(holdout[holdout["fund"] == fund]["variant"])]]
        y = np.arange(len(sub))
        ax.barh(y - 0.19, sub["discovery_sharpe"], height=0.36,
                color=fs.SERIES[0], label="2021-2022 (tuning)")
        ax.barh(y + 0.19, sub["holdout_sharpe"], height=0.36,
                color=fs.SERIES[2], label="2023 (holdout)")
        for yi, picked in enumerate(sub["selected_by_tuning"]):
            if picked:
                ax.text(-0.02, yi, "→", ha="right", va="center",
                        fontsize=12, color=fs.INK,
                        transform=ax.get_yaxis_transform())
        ax.set_yticks(y)
        ax.set_yticklabels([v.replace(" lexicon", "") for v in sub.index]
                           if ax is axes[0] else [], fontsize=7.5)
        ax.set_title(fund.replace("Equity ", ""), fontsize=9, loc="left",
                     color=fs.INK)
        ax.set_xlabel("Sharpe ratio")
        ax.axvline(0, color=fs.BASELINE, linewidth=0.8)
        ax.grid(axis="y", visible=False)
        ax.invert_yaxis()
    axes[0].legend(frameon=False, fontsize=7.5, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), ncol=2)
    fs.finish(fig, path, SOURCE + " Arrow marks the variant tuning selects.")


def rebalance_frequency(study: pd.DataFrame, path: str) -> None:
    """Sharpe against turnover for each rebalance schedule."""
    order = ["weekly", "fortnightly", "monthly", "quarterly"]
    methods = list(dict.fromkeys(study["method"]))
    fig, (ax,) = fs.new_figure(
        "How often should the fund trade?",
        "Out-of-sample Sharpe ratio of the combined funds under four "
        "rebalance schedules, net of 10 bp of one-way turnover, against the "
        "turnover each schedule generates. Points run weekly, fortnightly, "
        "monthly, quarterly; the ring marks each method's best schedule. "
        "Quarterly is worst everywhere; beyond that the best schedule depends "
        "on how much the optimiser moves the weights.",
        height=3.6,
    )
    markers = ["o", "s", "^", "D"]
    for slot, method in enumerate(methods):
        sub = study[study["method"] == method].set_index("frequency").loc[order]
        colour = fs.SERIES[slot % len(fs.SERIES)]
        ax.plot(sub["annual_turnover"], sub["sharpe_net_costs"], color=colour,
                linewidth=1.0, marker=markers[slot % len(markers)],
                markersize=4, alpha=0.9)
        best = sub["sharpe_net_costs"].idxmax()
        ax.scatter([sub.loc[best, "annual_turnover"]],
                   [sub.loc[best, "sharpe_net_costs"]], s=58,
                   facecolors="none", edgecolors=colour, linewidths=1.4,
                   zorder=5)
        fs.direct_label(ax, sub["annual_turnover"].iloc[-1],
                        sub["sharpe_net_costs"].iloc[-1], f"  {method}", colour)
    ax.set_xlabel("Portfolio turnover (one-way, times per year)")
    ax.set_ylabel("Sharpe ratio, net of costs")
    ax.margins(x=0.30)
    fs.finish(fig, path, SOURCE)


def extension_comparison(extensions: pd.DataFrame, path: str) -> None:
    """Sharpe of every fusion variant, gross and net of transaction costs."""
    df = extensions.copy()
    funds_shown = list(dict.fromkeys(df["fund"]))
    fig, axes = fs.new_figure(
        "Sentiment variants against the base fund",
        "Out-of-sample Sharpe ratio of each equity fund under the fixed tilt "
        "and the adaptive-direction tilt, on the plain and the "
        "finance-extended lexicon. Solid bars are gross; the darker inset "
        "charges 10 bp of one-way turnover at each rebalance. The dashed "
        "line marks the base fund.",
        n_axes=len(funds_shown), height=3.8,
    )
    order = list(dict.fromkeys(df["variant"]))
    # One shared x-scale across the panels: different scales would make a
    # weaker variant look stronger than it is.
    xmax = 1.15 * df["sharpe"].max()
    for ax, fund in zip(axes, funds_shown):
        sub = df[df["fund"] == fund].set_index("variant").loc[order]
        y = np.arange(len(sub))
        ax.barh(y, sub["sharpe"], color=fs.SERIES[0], height=0.62,
                label="gross")
        ax.barh(y, sub["sharpe_net_costs"], color=fs.SERIES[4], height=0.26,
                label="net of 10 bp")
        ax.axvline(sub["sharpe"].iloc[0], color=fs.INK, linewidth=0.9,
                   linestyle="--", zorder=5)
        for yi, v in enumerate(sub["sharpe"]):
            ax.text(v + 0.012, yi, f"{v:.2f}", va="center", fontsize=7.5,
                    color=fs.INK_2)
        ax.set_yticks(y)
        ax.set_yticklabels(sub.index if ax is axes[0] else [], fontsize=7.5)
        ax.set_title(fund.replace("Equity ", ""), fontsize=9,
                     color=fs.INK, loc="left")
        ax.set_xlabel("Sharpe ratio")
        ax.set_xlim(0, xmax)
        ax.grid(axis="y", visible=False)
        ax.invert_yaxis()
    axes[0].legend(frameon=False, fontsize=7.5, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), ncol=2)
    fs.finish(fig, path, SOURCE)


def lexicon_effect(effect: pd.DataFrame, path: str) -> None:
    """What the finance lexicon did to the share of headlines scored neutral."""
    fig, (ax,) = fs.new_figure(
        "The finance lexicon cuts VADER's false neutrals",
        "Share of the 146,830 aligned headlines scoring within +/-0.05 - "
        "VADER's own neutral band - before and after merging "
        f"{int(effect['n_terms_added'].max())} finance terms into the "
        "lexicon. Only 1,831 of the 33,033 distinct headline tokens carry a "
        "VADER score at all.",
        height=2.8,
    )
    y = np.arange(len(effect))
    ax.barh(y, 100 * effect["neutral_share"], color=[fs.SERIES[0], fs.SERIES[1]],
            height=0.55)
    for yi, v in enumerate(effect["neutral_share"]):
        ax.text(100 * v + 0.6, yi, f"{v:.1%}", va="center", fontsize=8.5,
                color=fs.INK_2, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(effect["lexicon"], fontsize=8.5)
    ax.set_xlabel("Headlines scored neutral (%)")
    ax.grid(axis="y", visible=False)
    ax.invert_yaxis()
    fs.finish(fig, path, SOURCE)


def fusion_before_after(base: dict, tilted: dict, label: str, path: str) -> None:
    """Growth of $1 for a base fund and its sentiment-tilted version."""
    fig, (ax,) = fs.new_figure(
        f"Sentiment fusion: {label}",
        "Growth of $1 for the base fund and the same fund with the sector "
        "sentiment tilt applied at each rebalance. The tilt reads sentiment "
        "lagged one trading day, so no headline is used before it is public.",
        height=3.4,
    )
    for slot, (name, res) in enumerate([("base", base), ("+ sentiment tilt", tilted)]):
        colour = fs.SERIES[slot]
        g = res["growth"]
        ax.plot(g.index, g.to_numpy(), color=colour, linewidth=1.5)
        fs.direct_label(ax, g.index[-1], g.iloc[-1], f"  {name}  ${g.iloc[-1]:.2f}", colour)
    ax.axhline(1.0, color=fs.BASELINE, linewidth=0.8, zorder=0)
    ax.set_ylabel("Value of $1 (USD)")
    ax.set_xlabel("Date")
    fs.year_axis(ax)
    ax.margins(x=0.30)
    fs.finish(fig, path, SOURCE)
