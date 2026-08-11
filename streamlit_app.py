"""Spotlight - systematic multi-asset funds with news-sentiment analytics.

The investor journey: compare the funds, read a fact sheet, build an
allocation across funds, and read the news-sentiment analytics.

Everything on screen is precomputed by scripts/run_part_b.py and committed
under results/. The app re-runs no backtest and loads no sentiment-scoring
library - it only reads CSVs - so it starts fast on Streamlit Community
Cloud's free tier.

Run locally:   streamlit run streamlit_app.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"

# Spotlight palette - the report figure design system (src/figstyle.py), kept
# literal here so the deployed app imports nothing from src beyond data access.
# The seven extended slots exist for the sector stack; every pair in the twelve
# is separation-checked under colour-blind vision by tools/check_palette.py.
SERIES = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7"]
SERIES_EXTENDED = SERIES + ["#d7b2b8", "#9d0005", "#73c4f9", "#9c834e",
                            "#d3bcfb", "#074951", "#f3bb8b"]
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e1e0d9"


def chart_colours(n: int) -> list[str]:
    """Exactly `n` categorical colours, never cycled.

    Streamlit requires the colour list to match the column count exactly, so
    every chart whose series count depends on user selection must size its
    palette the same way. Slicing the five brand slots was the bug behind
    three separate crashes: picking six funds, or six sectors, asked for more
    colours than the slice returned.
    """
    if n > len(SERIES_EXTENDED):
        raise ValueError(f"{n} series exceeds the "
                         f"{len(SERIES_EXTENDED)} validated colour slots")
    return SERIES_EXTENDED[:n]
TRADING_DAYS = {"Equity": 252, "Crypto": 365, "Combined": 252}

st.set_page_config(page_title="Spotlight - Systematic Funds",
                   page_icon="🔦", layout="wide")


# --- data ------------------------------------------------------------------

def _artifact_stamp() -> tuple:
    """Modification times of every artifact the app reads.

    Passed into the cached loader so that re-running scripts/run_part_b.py
    invalidates the cache. Without it a long-lived server keeps serving the
    frames it loaded at startup, and a pipeline change that adds a column
    surfaces as a KeyError against data the app can no longer see.
    """
    paths = sorted(DATA.glob("*.csv")) + sorted(TABLES.glob("*.csv"))
    return tuple((p.name, p.stat().st_mtime_ns) for p in paths)


@st.cache_data(show_spinner="Loading fund data...")
def load_artifacts(stamp: tuple) -> dict:
    returns = pd.read_csv(DATA / "fund_returns.csv", index_col="date",
                          parse_dates=True)
    weights = pd.read_csv(DATA / "fund_weights.csv", parse_dates=["date"])
    metrics = pd.read_csv(TABLES / "performance_metrics.csv")
    sentiment = pd.read_csv(DATA / "sector_sentiment_index.csv",
                            parse_dates=["date"])
    fusion = pd.read_csv(TABLES / "fusion_before_after.csv")
    diagnostics = pd.read_csv(TABLES / "sentiment_signal_diagnostics.csv")
    coverage = pd.read_csv(TABLES / "sentiment_coverage.csv")
    sentiment_ext = pd.read_csv(DATA / "sector_sentiment_index_extended.csv",
                                parse_dates=["date"])
    extensions = pd.read_csv(TABLES / "extension_comparison.csv")
    lexicon = pd.read_csv(TABLES / "finance_lexicon.csv")
    lexicon_effect = pd.read_csv(TABLES / "lexicon_effect.csv")
    fear_greed = pd.read_csv(DATA / "fear_greed_index.csv", parse_dates=["date"])
    holdout = pd.read_csv(TABLES / "discovery_holdout.csv")
    return {"returns": returns, "weights": weights, "metrics": metrics,
            "sentiment": sentiment, "fusion": fusion,
            "diagnostics": diagnostics, "coverage": coverage,
            "sentiment_ext": sentiment_ext, "extensions": extensions,
            "lexicon": lexicon, "lexicon_effect": lexicon_effect,
            "fear_greed": fear_greed, "holdout": holdout}


def metrics_from_returns(r: pd.Series, days: int = 252) -> dict:
    r = r.dropna()
    growth = (1.0 + r).cumprod()
    ann_vol = r.std() * np.sqrt(days)
    return {
        "ann_return": growth.iloc[-1] ** (days / len(r)) - 1.0,
        "ann_vol": ann_vol,
        "sharpe": (r.mean() * days) / ann_vol if ann_vol else np.nan,
        "max_drawdown": (growth / growth.cummax() - 1.0).min(),
        "growth": growth,
    }


def growth_frame(returns: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    sub = returns[names].dropna(how="all")
    return (1.0 + sub.fillna(0.0)).cumprod()


def pct(x: float) -> str:
    return f"{x:.1%}"


# --- app -------------------------------------------------------------------

art = load_artifacts(_artifact_stamp())
returns, metrics = art["returns"], art["metrics"]
fund_names = list(metrics["fund"])

with st.sidebar:
    st.title("🔦 Spotlight")
    st.caption("Systematic multi-asset funds, built from prices and news.")
    st.markdown(
        "**Who it is for.** Working professionals and early-career investors "
        "who want a rules-based portfolio without doing the research "
        "themselves."
    )
    st.divider()
    first = metrics["first_live_date"].min()
    last = metrics["last_date"].max()
    st.metric("Funds on offer", len(fund_names))
    st.metric("Out-of-sample track record", f"{first} to {last}")
    st.caption(
        "All performance shown is out-of-sample: weights at every monthly "
        "rebalance are estimated only from returns before that date. "
        "Risk-free rate assumed zero; transaction costs excluded."
    )
    st.divider()
    st.caption("Past performance does not predict future returns. This is a "
               "university coursework prototype, not investment advice.")

tab_compare, tab_sheet, tab_build, tab_news, tab_lab = st.tabs(
    ["Compare funds", "Fund fact sheet", "Build your allocation",
     "News sentiment", "Under the hood"]
)


# --- 1. compare ------------------------------------------------------------

with tab_compare:
    st.subheader("Every fund, side by side")
    st.write(
        "Each fund is one asset family run through one optimisation method. "
        "Pick the funds you want to compare; the table and the chart update "
        "together."
    )

    families = st.multiselect("Asset family", sorted(metrics["family"].unique()),
                              default=sorted(metrics["family"].unique()))
    view = metrics[metrics["family"].isin(families)] if families else metrics

    show = view[["fund", "family", "method", "ann_return", "ann_vol", "sharpe",
                 "max_drawdown", "growth_of_1", "n_assets_held"]].copy()
    st.dataframe(
        show, hide_index=True, width="stretch",
        column_config={
            "fund": "Fund", "family": "Family", "method": "Method",
            "ann_return": st.column_config.NumberColumn("Return p.a.", format="%.1f%%"),
            "ann_vol": st.column_config.NumberColumn("Volatility p.a.", format="%.1f%%"),
            "sharpe": st.column_config.NumberColumn("Sharpe", format="%.2f"),
            "max_drawdown": st.column_config.NumberColumn("Max drawdown", format="%.1f%%"),
            "growth_of_1": st.column_config.NumberColumn("$1 grew to", format="$%.2f"),
            "n_assets_held": st.column_config.NumberColumn("Holdings", format="%d"),
        },
    )
    st.caption(
        "Return p.a. is the geometric annualised return; the Sharpe ratio uses "
        "the arithmetic mean, so a very volatile fund can show a positive "
        "Sharpe and still lose money - the crypto funds run near 80% "
        "annualised volatility, where that gap is large."
    )

    default = [n for n in fund_names if n.startswith("Combined")][:4]
    chosen = st.multiselect("Chart these funds", fund_names,
                            default=default or fund_names[:4])
    if chosen:
        st.line_chart(growth_frame(returns, chosen), height=380,
                      color=chart_colours(len(chosen)),
                      x_label="Date", y_label="Value of $1 (USD)")
        st.caption(
            "Growth of $1 invested at each fund's first live backtest date. "
            "Crypto-only funds start a few days earlier because crypto trades "
            "seven days a week."
        )


# --- 2. fact sheet ---------------------------------------------------------

with tab_sheet:
    fund = st.selectbox("Fund", fund_names, index=0)
    row = metrics[metrics["fund"] == fund].iloc[0]
    days = TRADING_DAYS[row["family"]]
    r = returns[fund].dropna()
    m = metrics_from_returns(r, days)

    st.subheader(fund)
    st.caption(
        f"{row['family']} assets, {row['method']} optimisation. Live from "
        f"{row['first_live_date']} to {row['last_date']} "
        f"({int(row['n_days'])} trading days, annualised on {days} days)."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("$1 grew to", f"${m['growth'].iloc[-1]:.2f}")
    c2.metric("Return p.a.", pct(m["ann_return"]))
    c3.metric("Volatility p.a.", pct(m["ann_vol"]))
    c4.metric("Sharpe ratio", f"{m['sharpe']:.2f}")
    c5.metric("Max drawdown", pct(m["max_drawdown"]))

    left, right = st.columns(2)
    with left:
        st.markdown("**Growth of $1**")
        st.line_chart(m["growth"].rename("Value of $1"), height=280,
                      color=SERIES[0], x_label="Date", y_label="USD")
    with right:
        st.markdown("**Drawdown**")
        dd = (m["growth"] / m["growth"].cummax() - 1.0) * 100
        st.area_chart(dd.rename("Drawdown (%)"), height=280,
                      color=SERIES[0], x_label="Date", y_label="% below peak")

    st.markdown("**Current holdings** - the target weights set at the most "
                "recent rebalance, which is what your money would buy today.")
    w = art["weights"]
    w_fund = w[w["fund"] == fund]
    latest = w_fund[w_fund["date"] == w_fund["date"].max()]
    latest = latest.sort_values("weight", ascending=False)
    hold_l, hold_r = st.columns([2, 3])
    with hold_l:
        st.dataframe(
            latest[["asset", "weight"]].head(15), hide_index=True,
            width="stretch",
            column_config={
                "asset": "Asset",
                "weight": st.column_config.ProgressColumn(
                    "Weight", format="%.1f%%", min_value=0.0,
                    max_value=float(latest["weight"].max())),
            },
        )
    with hold_r:
        top = latest.head(12).set_index("asset")["weight"] * 100
        st.bar_chart(top.rename("Weight (%)"), height=340, color=SERIES[1],
                     x_label="Weight (%)", y_label="Asset", horizontal=True)
    st.caption(f"Rebalanced on {latest['date'].iloc[0]:%d %b %Y}. "
               f"{len(latest)} positions carry a non-zero weight.")

    st.markdown("**How the holdings have shifted** - the same target weights "
                "at every rebalance, grouped into sectors so the shape is "
                "readable across 60 possible holdings.")
    if "sector" not in w_fund.columns:
        st.info("Sector labels are missing from results/data/fund_weights.csv. "
                "Re-run `python scripts/run_part_b.py` to rebuild it.")
    else:
        bands = (w_fund.pivot_table(index="date", columns="sector",
                                    values="weight", aggfunc="sum")
                 .fillna(0.0) * 100)
        # Every sector gets its own validated slot - see tools/check_palette.py.
        # Crypto is stacked last in dark ink because it is an asset class, not
        # a sector, and the reader should find it instantly.
        has_crypto = "Crypto" in bands.columns
        equity_bands = bands.drop(columns=["Crypto"]) if has_crypto else bands
        order = list(equity_bands.mean().sort_values(ascending=False).index)
        palette = chart_colours(len(order))
        plot = bands[order].copy()
        if has_crypto:
            plot["Crypto"] = bands["Crypto"]
            palette = palette + [INK_2]
        st.area_chart(plot, height=340, color=palette,
                      x_label="Rebalance date", y_label="Weight (%)")
        crypto_share = bands["Crypto"].mean() if has_crypto else 0.0
        st.caption(
            "Bands stack to 100% on every rebalance date, so a widening band "
            "means the fund holds more of that sector. This fund has averaged "
            f"{crypto_share:.1f}% in crypto across the backtest."
        )


# --- 3. build an allocation ------------------------------------------------

with tab_build:
    st.subheader("Put your money to work")
    st.write(
        "Split a starting amount across the funds. Spotlight rebalances your "
        "blend back to these shares whenever the underlying funds rebalance, "
        "so the blended track record below is what you would have earned."
    )

    amount = st.number_input("Amount to invest (USD)", min_value=100,
                             max_value=10_000_000, value=10_000, step=1_000)
    picks = st.multiselect(
        "Funds in your portfolio", fund_names,
        default=["Combined Maximum-Sharpe", "Combined Minimum-Variance"],
    )

    if not picks:
        st.info("Pick at least one fund to see your blended portfolio.")
    else:
        cols = st.columns(min(len(picks), 4))
        raw = {}
        for i, name in enumerate(picks):
            with cols[i % len(cols)]:
                raw[name] = st.slider(name, 0, 100, int(100 / len(picks)), 5,
                                      key=f"alloc_{name}")
        total = sum(raw.values())
        if total == 0:
            st.warning("Give at least one fund a non-zero share.")
        else:
            alloc = {k: v / total for k, v in raw.items()}
            if total != 100:
                st.caption(f"Shares sum to {total}%, so they are rescaled to "
                           "100% in the calculation below.")

            sub = returns[list(alloc)].dropna()
            blend = sub.mul(pd.Series(alloc)).sum(axis=1)
            days = max(TRADING_DAYS[metrics.loc[metrics["fund"] == n,
                                                "family"].iloc[0]] for n in alloc)
            bm = metrics_from_returns(blend, days)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Your portfolio today",
                      f"${amount * bm['growth'].iloc[-1]:,.0f}",
                      f"{bm['growth'].iloc[-1] - 1:+.1%} vs ${amount:,.0f}")
            k2.metric("Return p.a.", pct(bm["ann_return"]))
            k3.metric("Volatility p.a.", pct(bm["ann_vol"]))
            k4.metric("Max drawdown", pct(bm["max_drawdown"]))

            chart = pd.DataFrame({"Your blend": bm["growth"] * amount})
            for name in alloc:
                chart[name] = (1.0 + sub[name]).cumprod() * amount
            # The blend is the hero series, so it takes the dark ink and the
            # constituent funds take categorical slots behind it.
            st.line_chart(chart, height=380,
                          color=[INK] + chart_colours(len(chart.columns) - 1),
                          x_label="Date", y_label="Portfolio value (USD)")
            st.caption(
                f"Value of ${amount:,.0f} invested on {sub.index[0]:%d %b %Y}, "
                "your blend against each fund held alone. Blending lowers the "
                "swings when the funds do not move together."
            )

            fee = 0.01 * amount * bm["growth"].mean()
            st.caption(f"At a 1% annual management fee, Spotlight would have "
                       f"earned about ${fee:,.0f} a year on this account - the "
                       "business model behind the product.")


# --- 4. news sentiment -----------------------------------------------------

with tab_news:
    st.subheader("What the news is saying")
    st.write(
        "Spotlight scores every equity headline with VADER and averages the "
        "scores within each sector, equal-weighting the five tickers so one "
        "heavily covered name cannot speak for the sector. The index is a "
        "standalone analytic - read it as the tone of coverage, not a buy "
        "signal."
    )

    fg = art["fear_greed"].dropna(subset=["fear_greed_z"])
    latest = fg.iloc[-1]
    st.markdown("#### The market mood, in one number")
    g1, g2, g3 = st.columns([1, 1, 2])
    g1.metric("Fear and greed gauge", f"{latest['fear_greed_raw']:.0f} / 100",
              help="50 is neutral. Averaged across all 50 stocks.")
    g2.metric("Against its own history", f"{latest['fear_greed_z']:+.2f} sd",
              "greedier than usual" if latest["fear_greed_z"] > 0
              else "more fearful than usual")
    with g3:
        st.caption(
            "The raw gauge sits above neutral on 99% of days, because "
            "headline writers lean positive. Reading the level alone would "
            "call the market greedy through the COVID crash. Spotlight "
            "therefore shows it against its own history, where the fear "
            "episodes actually show up."
        )
    fg_smooth = st.select_slider("Gauge smoothing (trading days)",
                                 [1, 5, 21, 63], value=21, key="fg_smooth")
    gauge = fg.set_index("date")[["fear_greed_z"]].rolling(
        fg_smooth, min_periods=1).mean().rename(
        columns={"fear_greed_z": "Standard deviations from mean"})
    st.line_chart(gauge, height=260, color=SERIES[0],
                  x_label="Trading day", y_label="Standard deviations")
    st.divider()

    st.markdown("#### Sentiment by sector")
    use_ext = st.toggle(
        "Use the finance lexicon", value=False,
        help="Spotlight's extended VADER lexicon adds 46 market terms that "
             "plain VADER does not score, such as 'beat', 'downgrade', and "
             "'plunge'.")
    sent = art["sentiment_ext"] if use_ext else art["sentiment"]
    sectors = sorted(sent["sector"].unique())
    chosen_sec = st.multiselect("Sectors", sectors,
                                default=["Tech", "Energy", "Financials",
                                         "Healthcare", "Utilities"])
    smooth = st.select_slider("Smoothing (trading days)", [1, 5, 21, 63], value=21)

    if chosen_sec:
        wide = (sent[sent["sector"].isin(chosen_sec)]
                .pivot(index="date", columns="sector", values="sentiment")
                .rolling(smooth, min_periods=max(1, smooth // 3)).mean())
        st.line_chart(wide, height=380, color=chart_colours(wide.shape[1]),
                      x_label="Trading day", y_label="VADER compound score")
        st.caption(
            "VADER compound scores run from -1 to +1. Every sector averages "
            "positive: headline writing carries an optimistic bias, so the "
            "level matters less than the movement."
        )

    st.markdown("**How much news sits behind the index**")
    cov = art["coverage"].copy()
    st.dataframe(
        cov, hide_index=True, width="stretch",
        column_config={
            "sector": "Sector",
            "n_headlines": st.column_config.NumberColumn("Headlines", format="%d"),
            "n_tickers": st.column_config.NumberColumn("Tickers", format="%d"),
            "mean_compound": st.column_config.NumberColumn("Mean score", format="%.3f"),
            "neutral_share": st.column_config.NumberColumn("Scored neutral", format="%.1f%%"),
            "n_days_with_news": st.column_config.NumberColumn("Days with news", format="%d"),
        },
    )
    st.caption(
        "About half of all headlines score neutral under plain VADER - a "
        "general-purpose lexicon misses finance words such as 'downgrade' or "
        "'beat'. A neutral score means the model found nothing, not that the "
        "news was balanced."
    )

    st.divider()
    st.markdown("### Does the sentiment improve the funds?")
    st.write(
        "Spotlight tests a sector tilt: at each rebalance, weights move toward "
        "sectors whose sentiment is high relative to the others. The signal is "
        "lagged one trading day, so a Monday headline is first usable on "
        "Tuesday."
    )
    fus = art["fusion"]
    st.dataframe(
        fus, hide_index=True, width="stretch",
        column_config={
            "fund": "Fund",
            "ann_return": st.column_config.NumberColumn("Return p.a.", format="%.2f%%"),
            "ann_vol": st.column_config.NumberColumn("Volatility p.a.", format="%.2f%%"),
            "sharpe": st.column_config.NumberColumn("Sharpe", format="%.3f"),
            "max_drawdown": st.column_config.NumberColumn("Max drawdown", format="%.2f%%"),
            "growth_of_1": st.column_config.NumberColumn("$1 grew to", format="$%.3f"),
            "avg_turnover": st.column_config.NumberColumn("Avg turnover", format="%.3f"),
        },
    )

    diag = art["diagnostics"]
    st.markdown("**Why the tilt behaves as it does**")
    st.bar_chart(
        diag.set_index("sector")["corr_lagged_sentiment_vs_return"]
            .rename("Correlation"),
        height=320, color=SERIES[2], horizontal=True,
        x_label="Correlation with same-day sector return", y_label="Sector",
    )
    st.caption(
        "Correlation between the lagged sector sentiment index and the "
        "equal-weight sector return on the day the signal is usable. Most "
        "sectors are negative, so buying high-sentiment sectors leans the "
        "wrong way - the fusion result above is honest about that."
    )

# --- 5. under the hood (the extensions) ------------------------------------

with tab_lab:
    st.subheader("How Spotlight reads the news differently")
    st.write(
        "Two things separate Spotlight's sentiment work from an off-the-shelf "
        "VADER run. Both are measured against the plain baseline below rather "
        "than assumed to help."
    )

    st.markdown("#### 1. A finance lexicon, built from the headlines")
    eff = art["lexicon_effect"]
    e1, e2, e3 = st.columns(3)
    plain_row = eff.iloc[0]
    ext_row = eff.iloc[1]
    e1.metric("Headlines scored neutral", pct(ext_row["neutral_share"]),
              f"{ext_row['neutral_share'] - plain_row['neutral_share']:+.1%} "
              "vs plain VADER", delta_color="inverse")
    e2.metric("Finance terms added", int(ext_row["n_terms_added"]))
    e3.metric("Headlines rescored", pct(ext_row["headlines_rescored_share"]))
    st.caption(
        "Only 1,831 of the 33,033 distinct words in the headlines carry a "
        "VADER score. 'Earnings' appears 11,870 times and 'beat' 2,083 times, "
        "and plain VADER scores neither, so a headline like "
        "\"AbbVie Q4 EPS $2.21 Beats $2.19 Estimate\" reads as perfectly "
        "neutral. That is a false neutral, not balanced news."
    )

    with st.expander("See the lexicon, and the words deliberately left out"):
        lex = art["lexicon"]
        st.dataframe(lex, hide_index=True, width="stretch",
                     column_config={
                         "term": "Term",
                         "score": st.column_config.NumberColumn(
                             "Score", format="%.1f",
                             help="VADER's -4 to +4 scale"),
                         "category": "Why it was added",
                         "rationale": "Reasoning",
                     })
        st.caption(
            "Ambiguous words are excluded on purpose. 'Cut' is negative for a "
            "dividend and positive for an interest rate; 'buy' appears 15,806 "
            "times but almost always inside listicles ('3 stocks to buy'), "
            "which describe the writer rather than the company. Scoring those "
            "would add noise dressed up as signal."
        )

    st.markdown("#### 2. A tilt that learns which way to lean")
    st.write(
        "The obvious way to use sentiment is to buy the sectors the news likes. "
        "In this sample that loses money: the correlation between the lagged "
        "sentiment index and the return it can be traded on is negative in "
        "eight of ten sectors. Rather than hard-code the reverse - which would "
        "be fitting the answer to data Spotlight had already seen - the "
        "adaptive tilt re-estimates the relationship at every rebalance using "
        "only the prior year, and leans whichever way that window says."
    )

    ext = art["extensions"]
    st.dataframe(
        ext, hide_index=True, width="stretch",
        column_config={
            "fund": "Fund", "variant": "Variant",
            "sharpe": st.column_config.NumberColumn("Sharpe", format="%.3f"),
            "ann_return": st.column_config.NumberColumn("Return p.a.", format="%.2f%%"),
            "ann_vol": st.column_config.NumberColumn("Volatility p.a.", format="%.2f%%"),
            "max_drawdown": st.column_config.NumberColumn("Max drawdown", format="%.2f%%"),
            "sharpe_net_costs": st.column_config.NumberColumn(
                "Sharpe net of costs", format="%.3f",
                help="After charging 10 bp of one-way turnover at each rebalance"),
            "ann_return_net_costs": st.column_config.NumberColumn(
                "Return p.a. net", format="%.2f%%"),
            "avg_turnover": st.column_config.NumberColumn("Avg turnover", format="%.3f"),
        },
    )

    pivot = ext.pivot(index="variant", columns="fund", values="sharpe")
    st.bar_chart(pivot, height=340, color=chart_colours(pivot.shape[1]),
                 x_label="Variant", y_label="Sharpe ratio (gross)")
    st.caption(
        "The adaptive tilt on the plain lexicon beats the base fund on both "
        "equity funds and survives transaction costs. The two extensions do "
        "not stack, though: the finance lexicon makes the sentiment a better "
        "description of tone, but part of the contrarian edge came from "
        "VADER's blind spots, so combining them gives back the gain."
    )

    st.markdown("#### 3. Checking the winner was found, not fitted")
    st.write(
        "Comparing five variants over one period and keeping the best is "
        "itself a choice fitted to that period. The harder test: pick the "
        "winner using 2021-2022 only, then look at 2023, which played no part "
        "in the choice."
    )
    ho = art["holdout"]
    st.dataframe(
        ho[["fund", "variant", "discovery_sharpe", "holdout_sharpe",
            "sharpe_decay", "selected_by_tuning"]],
        hide_index=True, width="stretch",
        column_config={
            "fund": "Fund", "variant": "Variant",
            "discovery_sharpe": st.column_config.NumberColumn(
                "Sharpe 2021-22 (tuning)", format="%.3f"),
            "holdout_sharpe": st.column_config.NumberColumn(
                "Sharpe 2023 (holdout)", format="%.3f"),
            "sharpe_decay": st.column_config.NumberColumn(
                "Change", format="%.3f"),
            "selected_by_tuning": st.column_config.CheckboxColumn(
                "Tuning picked this"),
        },
    )
    st.caption(
        "The adaptive tilt on the plain lexicon is what tuning selects on "
        "2021-2022 for both funds, and it also ranks first on 2023 - so the "
        "ranking survived a period it was not chosen on. Two caveats belong "
        "with that: the holdout margin over the base fund is small (a few "
        "hundredths of a Sharpe point), and every variant of the "
        "Minimum-Variance fund decayed sharply into 2023, base included, "
        "which is the market regime rather than the tilt. One split of two "
        "funds is evidence, not proof."
    )

st.divider()
st.caption(
    "Spotlight - FINS5545 coursework prototype by Nuo Chen (z5640476). "
    "Funds are backtested out-of-sample on 2020-2023 course data; all figures "
    "are precomputed by scripts/run_part_b.py."
)
