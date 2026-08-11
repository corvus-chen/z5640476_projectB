"""Reproduce every Part B result end-to-end. Run from the project root:

    python scripts/run_part_b.py

Writes the app-readable CSVs to results/data/, the report tables to
results/tables/, and the exhibits to results/figures/. The deployed app reads
these artifacts and never recomputes anything here.
"""
from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features, portfolios as pf, sentiment as sn  # noqa: E402
from src import fusion as fu, figures as figs, finance_lexicon as fl  # noqa: E402

DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"

TILT_STRENGTH = 0.3
FUSION_METHODS = ("min_variance", "max_sharpe")
COST_BPS = 10.0  # one-way transaction cost charged on rebalance turnover
HOLDOUT_SPLIT = "2023-01-01"  # tune on 2021-2022, report the pick on 2023


def _step(msg: str, t0: float) -> float:
    print(f"  {msg} ({time.time() - t0:.1f}s)")
    return time.time()


def main() -> None:
    for d in (DATA, TABLES, FIGURES):
        d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("Station 1-2: data foundation")
    equities = etl.load_clean_equities()
    crypto = etl.load_clean_crypto()
    news = etl.load_clean_news()
    trading_days = equities["date"].drop_duplicates()
    ticker_sector = equities.drop_duplicates("ticker").set_index("ticker")["sector"]
    panels = {
        "Equity": features.returns_panel(equities),
        "Crypto": features.returns_panel(crypto),
        "Combined": features.combined_returns_panel(equities, crypto),
    }
    t0 = _step(f"{len(equities):,} equity rows, {len(crypto):,} crypto rows, "
               f"{len(news):,} unique headlines", t0)

    print("Station 3a: funds and out-of-sample backtests")
    funds = pf.build_funds(panels)
    metrics = pf.metrics_table(funds)
    metrics.to_csv(TABLES / "performance_metrics.csv", index=False)
    t0 = _step(f"{len(funds)} funds backtested, first live date "
               f"{metrics['first_live_date'].min()}", t0)

    # How often should the fund trade? Monthly is the headline schedule; this
    # shows what the alternatives would have earned, gross and net of costs.
    frequency_study = pf.rebalance_frequency_study(panels["Combined"],
                                                   cost_bps=COST_BPS)
    frequency_study.to_csv(TABLES / "rebalance_frequency.csv", index=False)
    best = frequency_study.loc[
        frequency_study.groupby("method")["sharpe_net_costs"].idxmax()]
    t0 = _step("rebalance-frequency study: best net schedule is "
               + ", ".join(f"{r.method} {r.frequency}" for r in best.itertuples()),
               t0)

    # Does fixing the covariance noise fix the result? Tests the Section 2
    # diagnosis rather than asserting it.
    shrinkage = pf.shrinkage_study({k: v for k, v in panels.items()
                                    if k in ("Equity", "Combined")})
    shrinkage.to_csv(TABLES / "shrinkage_study.csv", index=False)
    helped = shrinkage[shrinkage["change"] > 0.005]["method"].unique()
    t0 = _step("shrinkage study: helps " + (", ".join(helped) or "nothing")
               + f"; largest gain {shrinkage['change'].max():+.3f} Sharpe", t0)

    fund_returns = pd.DataFrame({n: r["returns"] for n, r in funds.items()})
    fund_returns.rename_axis("date").to_csv(DATA / "fund_returns.csv")

    weight_rows = []
    for name, res in funds.items():
        w = res["weights"].stack().rename("weight").reset_index()
        w.columns = ["date", "asset", "weight"]
        w.insert(0, "fund", name)
        # Carry the sector through so the app can aggregate without needing a
        # second lookup file; the coins have no sector and are their own band.
        w["sector"] = w["asset"].map(ticker_sector).fillna("Crypto")
        weight_rows.append(w[w["weight"] > 1e-6])
    pd.concat(weight_rows, ignore_index=True).to_csv(DATA / "fund_weights.csv", index=False)
    t0 = _step("wrote fund_returns.csv and fund_weights.csv", t0)

    print("Station 3b: sentiment model and sector index")
    aligned = features.assemble_headline_panel(news, trading_days)
    scored = sn.score_headlines(aligned)
    ticker_day = sn.ticker_day_sentiment(scored)
    index = sn.sector_sentiment_index(ticker_day, trading_days)
    index.to_csv(DATA / "sector_sentiment_index.csv", index=False)
    coverage = sn.coverage_summary(ticker_day, scored)
    coverage.to_csv(TABLES / "sentiment_coverage.csv", index=False)
    fear_greed = sn.fear_greed_index(ticker_day, trading_days)
    fear_greed.to_csv(DATA / "fear_greed_index.csv", index=False)
    sn.fear_greed_extremes(fear_greed).to_csv(
        TABLES / "fear_greed_extremes.csv", index=False)
    t0 = _step(f"{len(scored):,} headlines scored, "
               f"{scored['is_neutral'].mean():.1%} neutral, "
               f"{index['sector'].nunique()} sector indices", t0)

    print("Station 3c: sentiment fusion into the equity funds")
    diagnostics = fu.signal_diagnostics(index, panels["Equity"], ticker_sector)
    diagnostics.to_csv(TABLES / "sentiment_signal_diagnostics.csv", index=False)
    tilt = fu.make_sentiment_tilt(index, ticker_sector, strength=TILT_STRENGTH)

    fusion_tables, tilted_funds = [], {}
    for method in FUSION_METHODS:
        label = f"Equity {pf.METHOD_LABELS[method]}"
        base = funds[label]
        tilted = pf.oos_backtest(panels["Equity"], method=method, window=252,
                                 tilt_fn=tilt)
        tilted_funds[label] = tilted
        fusion_tables.append(fu.compare_before_after(base, tilted, 252, label))
    fusion = pd.concat(fusion_tables, ignore_index=True)
    fusion.to_csv(TABLES / "fusion_before_after.csv", index=False)

    fused_returns = pd.DataFrame({f"{n} + sentiment": r["returns"]
                                  for n, r in tilted_funds.items()})
    fused_returns.rename_axis("date").to_csv(DATA / "fusion_fund_returns.csv")
    t0 = _step(f"fusion tested on {len(FUSION_METHODS)} equity funds "
               f"(tilt strength {TILT_STRENGTH})", t0)

    # --- innovation extensions ------------------------------------------
    # Two extensions that chain: a finance lexicon that fixes VADER's false
    # neutrals, and a tilt that learns its own direction walk-forward. Both
    # are evaluated against the base fund and against each other, gross and
    # net of transaction costs.
    print("Extensions: finance lexicon and adaptive-direction tilt")
    lex = fl.lexicon()
    fl.as_table().to_csv(TABLES / "finance_lexicon.csv", index=False)
    scored_ext = sn.score_headlines(aligned, extra_lexicon=lex)
    index_ext = sn.sector_sentiment_index(
        sn.ticker_day_sentiment(scored_ext), trading_days)
    index_ext.to_csv(DATA / "sector_sentiment_index_extended.csv", index=False)

    lexicon_effect = pd.DataFrame([
        {"lexicon": "plain VADER", "n_terms_added": 0,
         "neutral_share": scored["is_neutral"].mean(),
         "mean_compound": scored["compound"].mean(),
         "sd_compound": scored["compound"].std()},
        {"lexicon": "VADER + finance terms", "n_terms_added": len(lex),
         "neutral_share": scored_ext["is_neutral"].mean(),
         "mean_compound": scored_ext["compound"].mean(),
         "sd_compound": scored_ext["compound"].std()},
    ])
    lexicon_effect["headlines_rescored_share"] = [
        0.0, float((scored["compound"] != scored_ext["compound"]).mean())]
    lexicon_effect.to_csv(TABLES / "lexicon_effect.csv", index=False)

    diag_ext = fu.signal_diagnostics(index_ext, panels["Equity"], ticker_sector)
    diag_ext.to_csv(TABLES / "sentiment_signal_diagnostics_extended.csv",
                    index=False)

    sector_rets = fu.sector_return_panel(panels["Equity"], ticker_sector)
    variants, ext_rows, sign_frames = {}, [], []
    for method in FUSION_METHODS:
        label = f"Equity {pf.METHOD_LABELS[method]}"
        specs = [("base (no sentiment)", None)]
        for tag, idx_v in [("plain", index), ("extended", index_ext)]:
            specs.append((f"fixed tilt / {tag} lexicon",
                          fu.make_sentiment_tilt(idx_v, ticker_sector,
                                                 strength=TILT_STRENGTH)))
            specs.append((f"adaptive tilt / {tag} lexicon",
                          fu.make_adaptive_sentiment_tilt(
                              idx_v, ticker_sector, sector_rets,
                              strength=TILT_STRENGTH)))
        for name, tilt_fn in specs:
            res = (funds[label] if tilt_fn is None else
                   pf.oos_backtest(panels["Equity"], method=method,
                                   window=252, tilt_fn=tilt_fn))
            variants[f"{label} | {name}"] = res
            gross = pf.performance_metrics(res["returns"], 252)
            net = pf.performance_metrics(
                fu.apply_costs(res["returns"], res["weights"], COST_BPS,
                               res.get("drifted_weights")), 252)
            ext_rows.append({
                "fund": label, "variant": name,
                "sharpe": gross["sharpe"], "ann_return": gross["ann_return"],
                "ann_vol": gross["ann_vol"],
                "max_drawdown": gross["max_drawdown"],
                "sharpe_net_costs": net["sharpe"],
                "ann_return_net_costs": net["ann_return"],
                "avg_turnover": fu.average_turnover(
                    res["weights"], res.get("drifted_weights")),
            })
            if tilt_fn is not None and hasattr(tilt_fn, "signs_"):
                sh = fu.sign_history(tilt_fn)
                if not sh.empty:
                    sh.insert(0, "variant", f"{label} | {name}")
                    sign_frames.append(sh)

    extensions = pd.DataFrame(ext_rows)
    extensions.to_csv(TABLES / "extension_comparison.csv", index=False)

    # Is the improvement bigger than noise, and what is the signal actually
    # doing? Both answers belong in the report whichever way they come out.
    lead_lag = fu.lead_lag_diagnostics(index, panels["Equity"], ticker_sector)
    lead_lag.to_csv(TABLES / "sentiment_lead_lag.csv", index=False)
    horizons = fu.horizon_diagnostics(index, panels["Equity"], ticker_sector,
                                      horizons=(1, 5, 21, 63))
    horizons.to_csv(TABLES / "sentiment_horizons.csv", index=False)

    sig_rows = []
    for method in FUSION_METHODS:
        label = f"Equity {pf.METHOD_LABELS[method]}"
        base_r = variants[f"{label} | base (no sentiment)"]["returns"]
        for name in ("adaptive tilt / plain lexicon", "fixed tilt / plain lexicon"):
            test = fu.bootstrap_sharpe_difference(
                base_r, variants[f"{label} | {name}"]["returns"], 252)
            test.update({"fund": label, "variant": name})
            sig_rows.append(test)
    significance = pd.DataFrame(sig_rows)[
        ["fund", "variant", "sharpe_base", "sharpe_variant", "difference",
         "ci_low", "ci_high", "p_value", "significant_5pct", "n_days"]]
    significance.to_csv(TABLES / "extension_significance.csv", index=False)
    t0 = _step(
        f"lead-lag: same-day corr {lead_lag['corr_same_day'].mean():+.4f} "
        f"({int((lead_lag['p_same_day'] < 0.05).sum())}/10 significant), "
        f"next-day {lead_lag['corr_next_day'].mean():+.4f} "
        f"({int((lead_lag['p_next_day'] < 0.05).sum())}/10); "
        f"tilt improvement significant in "
        f"{int(significance['significant_5pct'].sum())}/{len(significance)} tests; "
        f"horizon study {int(horizons['significant_corrected'].sum())}/"
        f"{len(horizons)} significant after correction",
        t0)

    # The harder test: pick the winner on 2021-2022 only, then report how that
    # pick did on 2023, which was never used to choose it.
    holdout_frames = []
    for method in FUSION_METHODS:
        label = f"Equity {pf.METHOD_LABELS[method]}"
        series = {name.split(" | ", 1)[1]: res["returns"]
                  for name, res in variants.items() if name.startswith(label)}
        ho = fu.discovery_holdout(series, split=HOLDOUT_SPLIT,
                                  days_per_year=252,
                                  baseline="base (no sentiment)")
        if not ho.empty:
            ho.insert(0, "fund", label)
            holdout_frames.append(ho)
    holdout = pd.concat(holdout_frames, ignore_index=True)
    holdout.to_csv(TABLES / "discovery_holdout.csv", index=False)
    if sign_frames:
        pd.concat(sign_frames, ignore_index=True).to_csv(
            DATA / "adaptive_tilt_directions.csv", index=False)
    t0 = _step(f"{len(lex)} lexicon terms, neutral share "
               f"{scored['is_neutral'].mean():.1%} -> "
               f"{scored_ext['is_neutral'].mean():.1%}; "
               f"{len(extensions)} fund variants compared "
               f"(gross and net of {COST_BPS:.0f}bp)", t0)

    print("Exhibits")
    combined = [pf.fund_name("Combined", m) for m in pf.METHODS]
    figs.growth_of_one(funds, combined, str(FIGURES / "growth_of_1_combined.png"),
                       "Growth of $1: combined equity and crypto funds")
    figs.drawdown(funds, "Combined Maximum-Sharpe",
                  str(FIGURES / "drawdown_combined_max_sharpe.png"))
    figs.weights_over_time(funds, "Combined Minimum-Variance",
                           str(FIGURES / "weights_combined_min_variance.png"),
                           ticker_sector=ticker_sector)
    figs.weights_over_time_across_methods(
        funds, "Combined", ["min_variance", "max_sharpe", "risk_parity"],
        str(FIGURES / "weights_combined_across_methods.png"),
        ticker_sector=ticker_sector)
    figs.sharpe_barplot(metrics, str(FIGURES / "sharpe_by_fund.png"))
    figs.rebalance_frequency(frequency_study,
                             str(FIGURES / "rebalance_frequency.png"))
    figs.sentiment_index(index, str(FIGURES / "sector_sentiment_index.png"),
                         sectors=["Tech", "Energy", "Financials", "Healthcare", "Utilities"])
    for method in FUSION_METHODS:
        label = f"Equity {pf.METHOD_LABELS[method]}"
        figs.fusion_before_after(
            funds[label], tilted_funds[label], label,
            str(FIGURES / f"fusion_{method}.png"))
    figs.extension_comparison(extensions, str(FIGURES / "extension_comparison.png"))
    figs.lexicon_effect(lexicon_effect, str(FIGURES / "lexicon_effect.png"))
    figs.fear_greed(fear_greed, sn.fear_greed_extremes(fear_greed),
                    str(FIGURES / "fear_greed_index.png"))
    figs.discovery_holdout(holdout, str(FIGURES / "discovery_holdout.png"))
    _step(f"{len(list(FIGURES.glob('*.png')))} figures written", t0)

    print("\nFund performance (out-of-sample):")
    show = metrics[["fund", "ann_return", "ann_vol", "sharpe", "max_drawdown"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    print("\nExtension comparison (Sharpe, gross and net of costs):")
    print(extensions[["fund", "variant", "sharpe", "sharpe_net_costs",
                      "avg_turnover"]]
          .to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    print(f"\nDiscovery (to {HOLDOUT_SPLIT}) vs holdout:")
    print(holdout[["fund", "variant", "discovery_sharpe", "holdout_sharpe",
                   "sharpe_decay", "selected_by_tuning"]]
          .to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nArtifacts written under results/. Next: streamlit run streamlit_app.py")


if __name__ == "__main__":
    main()
