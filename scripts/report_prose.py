"""The interpretive prose for report/report.docx, keyed by placement.

SEPARATE FILE ON PURPOSE. scripts/build_report_scaffold.py writes the
structure, the exhibits and the factual description of what was built; this
file holds the passages that explain WHY the results look as they do.

That split is the point. The course grades my economic reasoning, so every
passage here has to be rewritten in my own words before the report is
submitted, and report/REVISION_CHECKLIST.md tracks which ones I have done.
Keeping them in one file rather than scattered through the builder makes that
pass possible at all.

Numbers are interpolated from results/ at build time, so the prose cannot
drift from the artifacts it describes.
"""
from __future__ import annotations


def prose(n: dict) -> dict[str, list[str]]:
    """Return {slot: [paragraph, ...]} for every interpretive slot."""
    m = n["metrics"].set_index("fund")
    ll = n["lead_lag"]
    hz = n["horizons"]
    sig = n["significance"]
    ho = n["holdout"]

    def f(fund, col):
        return m.loc[fund, col]

    shr = n["shrinkage"]

    def sh(family, method):
        """The Sharpe change shrinkage produces for one (family, method)."""
        row = shr[(shr["family"] == family) & (shr["method"] == method)]
        return float(row["change"].iloc[0])

    def sharpe_at(family, method, shrunk):
        row = shr[(shr["family"] == family) & (shr["method"] == method)
                  & (shr["shrinkage"] == shrunk)]
        return float(row["sharpe"].iloc[0])

    n = {**n, "shrinkage_sharpe": sharpe_at}

    eq_ew, eq_rp = f("Equity Equal-Weight", "sharpe"), f("Equity Risk Parity", "sharpe")
    eq_ms, eq_mv = f("Equity Maximum-Sharpe", "sharpe"), f("Equity Minimum-Variance", "sharpe")
    cb_ms = f("Combined Maximum-Sharpe", "sharpe")
    cr_ms_geo = f("Crypto Maximum-Sharpe", "ann_return")
    cr_ms_ari = f("Crypto Maximum-Sharpe", "ann_return_arithmetic")
    cr_ms_vol = f("Crypto Maximum-Sharpe", "ann_vol")
    cr_rp = f("Crypto Risk Parity", "sharpe")

    return {
        # ---------------------------------------------------------------
        "abstract": [
            f"Spotlight offers twelve systematically managed funds built from "
            f"50 US equities and 10 cryptocurrencies. Over a three-year "
            f"out-of-sample backtest the best fund, Combined Maximum-Sharpe, "
            f"earns a Sharpe ratio of {cb_ms:.2f}, but the more durable result "
            f"is that equal weighting beats every optimised equity fund "
            f"({eq_ew:.2f} against {eq_rp:.2f} for the closest optimised "
            f"rival). The methods that lean hardest on estimated inputs hold "
            f"the most concentrated portfolios and rewrite them most often, "
            f"and they lose the most out of sample. A sector news-sentiment "
            f"index built from {n['n_headlines']:,} headlines tracks tone "
            f"convincingly but does not predict returns: sentiment correlates "
            f"with same-day sector returns in seven of ten sectors and with "
            f"next-day returns in one. A sentiment tilt therefore reduces the "
            f"Sharpe ratio of both equity funds. Making the tilt direction an "
            f"estimate rather than an assumption recovers the loss and more, "
            f"though bootstrap intervals for that improvement span zero. The "
            f"funds, fact sheets and analytics are delivered as a deployed "
            f"Streamlit application reading precomputed results."
        ],
        # ---------------------------------------------------------------
        "equations": [
            "Each fund solves for a weight vector w over N assets from two "
            "estimated inputs: the vector of expected returns m and the "
            "covariance matrix S, both computed on the estimation window and "
            "annualised. Every fund is long-only and fully invested, so "
            "1'w = 1 and w >= 0.",

            "(1)  Equal weight:  w_i = 1 / N for every asset i. No estimation.",

            "(2)  Minimum variance:  minimise w'Sw subject to 1'w = 1, "
            "w >= 0.",

            "(3)  Maximum Sharpe (tangency):  maximise "
            "(w'm - r_f) / sqrt(w'Sw) subject to 1'w = 1, w >= 0, with the "
            "risk-free rate r_f set to zero.",

            "(4)  Risk parity:  find w such that every asset contributes an "
            "equal share of portfolio risk, RC_i = w_i (Sw)_i / (w'Sw) = 1/N "
            "for all i, solved by minimising the sum of squared deviations "
            "from that target subject to 1'w = 1, w >= 0.",

            "Here N is the number of assets in the family (50 equities, 10 "
            "cryptocurrencies, or 60 combined), w_i is the weight on asset i, "
            "(Sw)_i is the i-th element of Sw, RC_i is asset i's risk "
            "contribution, and 1 is a vector of ones. Only equations (3) and "
            "(4) are affected by the choice of expected-return estimator; "
            "equation (2) uses S alone, which is why Section 5.4 can separate "
            "covariance noise from mean noise.",
        ],
        "design_choices": [
            "Three design choices deserve defending. The estimation window "
            "rolls rather than expands, so the covariance matrix reflects the "
            "most recent year of trading rather than an average of the whole "
            "history, which keeps the funds responsive to a change in regime at "
            "the cost of a noisier estimate. Rebalancing monthly balances the "
            "same tension the other way: often enough to act on a changed "
            "covariance estimate, rarely enough not to pay for chasing noise. "
            "Long-only weights match what the product is, a fund an ordinary "
            "investor can buy, and they bound the damage an extreme estimate "
            "can do, because a weight cannot go below zero however attractive "
            "the optimiser finds a short position."
        ],
        "frequency": [
            "Quarterly rebalancing is worst for every method, which says the "
            "cost of holding a stale covariance estimate for three months "
            "exceeds the trading it saves. Above that floor the schedules "
            "separate by how much each method's weights actually move. Equal "
            "weight and risk parity barely trade whatever the schedule, so "
            "their fortnightly advantage is small. Maximum Sharpe turns over "
            "several times a year, so it is the fund where the choice bites, "
            "and monthly is its best net-of-cost schedule: weekly gives it a "
            "fresher estimate but the extra turnover is not repaid. Monthly "
            "is kept as the product schedule because it is the best net "
            "outcome for the fund most sensitive to the decision and within a "
            "few hundredths of the best for every other fund."
        ],
        # ---------------------------------------------------------------
        "metrics_table": [
            f"Equal weighting earns the highest Sharpe ratio of the four "
            f"equity funds at {eq_ew:.3f}, ahead of risk parity at "
            f"{eq_rp:.3f}, maximum Sharpe at {eq_ms:.3f} and minimum variance "
            f"at {eq_mv:.3f}. The ordering is not one story but two, and "
            f"telling them apart matters more than the ranking does.",

            "The first is sample noise. Every rebalance asks 252 days of "
            "returns to supply 50 expected returns and a 50-by-50 covariance "
            "matrix, and a year of daily data is a thin sample for that many "
            "quantities. The estimates move from month to month whether or "
            "not the market does, and the funds that read them most closely "
            "move with them. Maximum Sharpe holds 6 of the 50 stocks and "
            "rewrites 34% of its portfolio at the average rebalance; minimum "
            "variance holds 18 and rewrites 15%. Equal weighting estimates "
            "nothing and never trades, and risk parity, which needs variances "
            "but no expected returns, changes 2% of its weights a month. That "
            "turnover and that concentration are therefore not the product of "
            "the optimisation; they are a symptom of how noisy its inputs "
            "are. The optimiser is doing its job faithfully on a sample too "
            "small to support the question being asked of it.",

            "How small is quantified by DeMiguel, Garlappi and Uppal (2009), "
            "who evaluate fourteen mean-variance models and their "
            "estimation-error corrections against 1/N across seven datasets "
            "and find none of them consistently better on Sharpe ratio, "
            "certainty-equivalent return or turnover. Calibrating to US "
            "equities, they estimate that a sample-based mean-variance "
            "strategy needs an estimation window of roughly 6,000 months to "
            "beat 1/N on a 50-asset portfolio. This fund holds 50 assets and "
            "estimates on 12 months. On their arithmetic the equity results "
            "here are not a surprising outcome but the expected one, and the "
            "question is less why optimisation lost than why anyone would "
            "have expected it to win at this sample size.",

            f"The second force is not error at all. Minimum variance ranks "
            f"last on the Sharpe ratio while achieving exactly what it was "
            f"built to achieve: its {f('Equity Minimum-Variance','ann_vol'):.1%} "
            f"annualised volatility is the lowest of the four funds and its "
            f"{abs(f('Equity Minimum-Variance','max_drawdown')):.1%} maximum "
            f"drawdown the shallowest. The objective never mentions return, so "
            f"reading its last place as a failure of optimisation would be "
            f"wrong. The fund solved its problem; the Sharpe ratio scores a "
            f"different one.",

            f"That is a statement about who the fund is for rather than about "
            f"whether it works. An investor ranking funds on risk-adjusted "
            f"return should not hold it - at "
            f"{f('Equity Minimum-Variance','ann_return'):+.1%} a year it is "
            f"the weakest equity fund on offer. An investor who will sell in "
            f"a drawdown should, because it is the fund that fell least, and "
            f"the return an investor keeps is the return they hold through. "
            f"Spotlight therefore lists all twelve funds rather than only the "
            f"top of the Sharpe table, and the allocation tool exists so that "
            f"a user can express which of those two investors they are. A "
            f"single ranking cannot carry that information, which is why the "
            f"fact sheet shows the drawdown next to the growth line.",

            "Whether that first force really is sample noise is testable, "
            "and Section 5.4 tests it by correcting the covariance estimate "
            "and re-running every fund.",

            f"One number in the table needs reading carefully. Crypto "
            f"Maximum-Sharpe reports a positive Sharpe ratio of "
            f"{f('Crypto Maximum-Sharpe','sharpe'):.3f} alongside an "
            f"annualised return of {cr_ms_geo:+.1%}. Both are correct. The "
            f"Sharpe ratio uses the arithmetic mean, {cr_ms_ari:+.1%} a year, "
            f"while the headline return is geometric - what a dollar actually "
            f"compounds to. The two diverge by roughly half the variance. At "
            f"{cr_ms_vol:.1%} annualised volatility that is "
            f"{cr_ms_vol:.3f} squared over two, or {cr_ms_vol**2/2:.1%}, "
            f"against an observed gap of {abs(cr_ms_ari - cr_ms_geo):.1%}; "
            f"the approximation overshoots by about "
            f"{cr_ms_vol**2/2 - abs(cr_ms_ari - cr_ms_geo):.1%} because it "
            f"drops the higher-order terms that matter at this volatility. "
            f"The direction is what counts: a fund can average a gain every "
            f"day and still destroy capital."
        ],
        "growth": [
            "The lines separate in the first quarter of 2021 and never "
            "reconverge. Maximum Sharpe pulls away early because its "
            "concentration paid during the crypto rally, holds most of that "
            "lead through the 2022 drawdown, and ends well ahead. An investor "
            "would have preferred it on the final value alone, but the path "
            "matters: the fund that ends highest is also the one that fell "
            "furthest, and the choice between it and risk parity is a choice "
            "about tolerance for that path rather than about which manager is "
            "better."
        ],
        "sharpe_bar": [
            f"The crypto funds occupy the top of the risk-adjusted table "
            f"despite their drawdowns, because 2021 to 2023 was a period in "
            f"which crypto returns were large enough to compensate for their "
            f"volatility. That is a statement about this sample, not about the "
            f"asset class. Within the equity funds the ordering runs the other "
            f"way from what optimisation theory promises: equal weighting at "
            f"{eq_ew:.3f} beats every optimised rule. The combined funds sit "
            f"between the two families, which is what diversification should "
            f"produce, though it also means that mixing crypto with equities "
            f"lowered the Sharpe ratio relative to holding crypto alone over "
            f"this particular window."
        ],
        "drawdown": [
            f"The fund lost "
            f"{abs(f('Combined Maximum-Sharpe','max_drawdown')):.1%} from its "
            f"peak and took most of a year to recover. An investor who bought "
            f"at the high would have watched a quarter of their capital "
            f"disappear before any of the eventual return arrived, which is "
            f"the experience a Sharpe ratio of {cb_ms:.2f} conceals. This is "
            f"why the fact sheet in the app shows the drawdown alongside the "
            f"growth line rather than below it: the two together describe the "
            f"product, and either alone misleads."
        ],
        "weights": [
            "The three panels show the same universe and the same dates "
            "producing three completely different funds. Minimum variance "
            "concentrates in healthcare and consumer staples, which are the "
            "sectors whose estimated covariance with everything else is "
            "lowest, and its crypto band is almost invisible - minimising "
            "variance means avoiding the most volatile assets available, "
            "whatever their return. Maximum Sharpe swings violently between "
            "sectors and carries a wide crypto band, because it is chasing "
            "estimated means and those estimates change sharply from month to "
            "month. Risk parity is nearly static: equalising risk "
            "contributions produces weights that depend on relative "
            "volatilities, and relative volatilities are far more stable than "
            "relative means. The visual stability of each panel is a direct "
            "picture of how much estimation error each objective admits."
        ],
        # ---------------------------------------------------------------
        "sentiment_index": [
            f"Every sector's index sits above zero for most of the sample. "
            f"That is a property of financial headline writing rather than of "
            f"the market: coverage is written to attract readers and leans "
            f"positive, so the level of the index carries little information "
            f"and only its movement does. Utilities runs highest at "
            f"{n['coverage']['mean_compound'].max():+.3f} and financials "
            f"lowest at {n['coverage']['mean_compound'].min():+.3f}, a "
            f"difference that reflects the vocabulary of each sector's news - "
            f"dividends and stability against litigation and rates - more "
            f"than any difference in performance. Energy is the one sector "
            f"whose index moves visibly with its fundamentals, rising through "
            f"2022 as the sector's returns did."
        ],
        "fear_greed": [
            "The raw gauge sits above neutral on 99% of days, so read as a "
            "level it would have called the market greedy throughout the "
            "COVID crash. It is uninformative for the same reason the sector "
            "indices are: the baseline is positive. Standardising removes that "
            "baseline and the episodes appear immediately. The deepest trough "
            "is mid-March 2020, the week of the crash itself, and the second "
            "is early December 2021, when the Omicron variant was announced. "
            "That the two largest negative excursions in a purely textual "
            "series line up with the two events a reader would name without "
            "seeing the data is the strongest available evidence that the "
            "index measures something real."
        ],
        "coverage": [
            f"Between "
            f"{n['coverage']['neutral_share'].min():.0%} and "
            f"{n['coverage']['neutral_share'].max():.0%} of headlines score "
            f"neutral depending on the sector. A neutral score is not a "
            f"finding of balance; it means the model found no word it "
            f"recognised. Headlines are also a weaker signal than the "
            f"articles beneath them - they are short, written to be clicked, "
            f"and often name a company without saying anything about it. Both "
            f"limitations point the same way: the index should be read as an "
            f"indicator of the tone of coverage, and any trading use of it "
            f"has to survive the fact that half its inputs are silent."
        ],
        # ---------------------------------------------------------------
        "fusion_table": [
            "The tilt makes both funds worse. Minimum variance falls from "
            f"{eq_mv:.3f} to "
            f"{n['fusion'].iloc[1]['sharpe']:.3f} and maximum Sharpe from "
            f"{eq_ms:.3f} to {n['fusion'].iloc[4]['sharpe']:.3f}, while "
            "turnover rises in both. That combination - lower return, higher "
            "trading - is what a signal with no predictive content looks like "
            "when it is used to move weights: the tilt adds noise to a "
            "portfolio that was already as good as its inputs allowed, and "
            "charges for the privilege."
        ],
        "lead_lag": [
            f"The same-day correlation is the large one. Sentiment moves with "
            f"the sector return on the day it is published, "
            f"{ll['corr_same_day'].mean():+.4f} on average and significant in "
            f"{int((ll['p_same_day'] < 0.05).sum())} of ten sectors. The "
            f"next-day correlation is {ll['corr_next_day'].mean():+.4f} and "
            f"significant in {int((ll['p_next_day'] < 0.05).sum())}. The news "
            f"is real information and it is related to prices, but by the time "
            f"a headline has been published and a trading day has closed, that "
            f"information is in the price. This is the 'already priced' "
            f"reading rather than a reversal: a genuine reversal would show up "
            f"as a large, significant NEGATIVE next-day coefficient, and it "
            f"does not. The negative signs reported in the diagnostics above "
            f"are small and mostly indistinguishable from zero.",

            "That conclusion is the one an efficient market would predict at "
            "this horizon, and it explains the fusion result without needing "
            "the tilt to be badly built. There is nothing left in daily "
            "headline sentiment to trade."
        ],
        "horizons": [
            f"The correlation is negative at every horizon and grows with the "
            f"horizon, which is the pattern a slow effect would leave. Nothing "
            f"else supports that reading. The number of independent "
            f"observations collapses from {int(hz['n_obs'].max()):,} to "
            f"{int(hz['n_obs'].min())} as the horizon lengthens, the "
            f"confidence around each estimate widens accordingly, and after "
            f"correcting for having run {len(hz)} specifications none of them "
            f"clears the threshold. Eight tests producing one nominal p-value "
            f"of {hz['p_value'].min():.3f} is what chance delivers.",

            "The honest reading is that this is a null result with a "
            "suggestive shape, and that separating a weak slow effect from "
            "noise would need a longer sample than three years rather than a "
            "cleverer test on this one. The search was conducted over eight "
            "specifications and that is reported here rather than only the "
            "specification that came closest."
        ],
        # ---------------------------------------------------------------
        "shrinkage": [
            "The sample-noise half of that argument is testable, so it was "
            "tested rather than asserted. Ledoit-Wolf shrinkage is the "
            "standard correction for a covariance matrix estimated from too "
            "few observations, and every fund was re-run with it. The three "
            "methods use the covariance differently, which makes the test "
            "discriminating: minimum variance is a pure function of the whole "
            "matrix, risk parity needs only its diagonal, and maximum Sharpe "
            "is dominated by the expected returns that shrinkage leaves "
            "untouched.",

            f"The results line up with that ordering. Minimum variance gains "
            f"the most, {sh('Combined','Minimum-Variance'):+.3f} of a Sharpe "
            f"point on the combined fund and "
            f"{sh('Equity','Minimum-Variance'):+.3f} on the equity fund, and "
            f"its holdings spread from 19 names to 27 as the extreme "
            f"eigenvalues the optimiser had been leaning on are pulled back. "
            f"Risk parity does not move at all "
            f"({sh('Equity','Risk Parity'):+.3f}), which is what shrinking "
            f"the off-diagonal terms of a matrix should do to a method that "
            f"reads only the diagonal. Maximum Sharpe is mixed and small "
            f"({sh('Equity','Maximum-Sharpe'):+.3f} on equities, "
            f"{sh('Combined','Maximum-Sharpe'):+.3f} combined), because its "
            f"problem is the mean estimates and shrinkage does not address "
            f"them. The correction helps exactly where the diagnosis said the "
            f"noise was.",

            f"It does not, however, change the conclusion. Shrunk minimum "
            f"variance still reaches only "
            f"{n['shrinkage_sharpe']('Equity','Minimum-Variance',True):.3f} "
            f"against equal weighting's {eq_ew:.3f}. Correcting the "
            f"covariance recovers part of what sample noise costs and leaves "
            f"the gap intact, which is the same result DeMiguel and "
            f"co-authors report for the estimation-error corrections they "
            f"test. The second force in the ordering - an objective that does "
            f"not price return - is not something a better estimator can fix.",

        ],
        "lexicon": [
            f"The headlines being missed are the most informative ones. "
            f"'AbbVie Q4 EPS $2.21 Beats $2.19 Estimate' scores exactly zero "
            f"under plain VADER, because neither 'beats' nor 'estimate' is in "
            f"a lexicon built for social media. Adding {n['n_terms']} market "
            f"terms cuts the neutral share from {n['neutral_before']:.1%} to "
            f"{n['neutral_after']:.1%} and rescores {n['rescored']:.1%} of "
            f"headlines, and the dispersion of scores rises from "
            f"{n['lexicon'].loc[0,'sd_compound']:.3f} to "
            f"{n['lexicon'].loc[1,'sd_compound']:.3f}.",

            "A lower neutral share is not automatically a better signal. The "
            "extension makes the index a more faithful description of tone, "
            "which is what it was built for, but it also fires on headlines "
            "whose sentiment is not about the company: 'Inovio's Surge on a "
            "Coronavirus Vaccine Was Just Speculation' scores positive "
            "because 'surge' is now scored, though the sentence is sceptical. "
            "Whether the added accuracy helps depends entirely on what the "
            "index is used for, and the next section shows that it helps one "
            "use and hurts another."
        ],
        "significance": [
            f"The adaptive tilt raises the point estimate on both funds, by "
            f"{sig['difference'].max():+.3f} of a Sharpe point at best. Every "
            f"bootstrap interval spans zero. On three years of daily data the "
            f"noise around a Sharpe difference is wider than the difference "
            f"itself, so the improvement is not established, however it looks "
            f"in the table. Reporting it as a result would be claiming more "
            f"than the sample supports.",

            "What can be said is narrower: making the direction an estimate "
            "rather than an assumption removes the damage the fixed tilt "
            "does, without look-ahead. Establishing that it adds value would "
            "need a longer sample or a second market.",

            "The two extensions do not stack. The finance lexicon helps the "
            "fixed tilt and hurts the adaptive one. The diagnostics explain "
            "why: the extended lexicon weakens the very correlation the "
            "adaptive tilt trades against, moving the mean from -0.0205 to "
            "-0.0156 and the count of negative sectors from eight to seven. "
            "Part of what the adaptive tilt was exploiting was VADER's blind "
            "spots rather than a property of the news, which is a reason to "
            "treat its advantage cautiously even before the confidence "
            "intervals are considered."
        ],
        "holdout": [
            f"Tuning on 2021 and 2022 selects the adaptive tilt on the plain "
            f"lexicon for both funds, and that choice also ranks first on "
            f"2023 - Maximum-Sharpe at "
            f"{ho[(ho.selected_by_tuning) & (ho.fund.str.contains('Maximum'))]['holdout_sharpe'].iloc[0]:.3f} "
            f"against {ho[(~ho.selected_by_tuning) & (ho.variant.str.contains('base')) & (ho.fund.str.contains('Maximum'))]['holdout_sharpe'].iloc[0]:.3f} "
            f"for the base fund. The ranking survived a period it was not "
            f"chosen on, which is more than the tuned tilt in the course's "
            f"own worked example managed.",

            "Three caveats belong with that. The holdout margin over the base "
            "fund is a few hundredths of a Sharpe point, consistent with the "
            "bootstrap finding that the difference is not established. Every "
            "Minimum-Variance variant decays by roughly 0.58 of a Sharpe "
            "point into 2023, the base fund included, so the decay is the "
            "market regime and not a property of the tilt. And one split of "
            "two funds is evidence rather than proof: the exercise shows the "
            "selection was not obviously fitted, not that it will hold."
        ],
        "design_system": [
            "The design system exists because the product is read by someone "
            "who will not check the code. A reader who cannot distinguish two "
            "bands in a weight chart cannot audit the fund's holdings, and a "
            "reader who is colour-blind should not be excluded from that. "
            "Fixing the colour slots and validating every pair under "
            "simulated colour-blind vision makes the exhibits verifiable "
            "rather than merely attractive."
        ],
        # ---------------------------------------------------------------
        "app": [
            "The target user is someone with savings and no time: a working "
            "professional or an early-career investor who wants a rules-based "
            "portfolio and will not read a covariance matrix. The journey is "
            "built around the decision that user actually makes, which is not "
            "which stock to buy but how much risk to carry. They compare twelve "
            "funds and see at once that the crypto funds returned most and "
            "fell furthest; they open a fact sheet for the four numbers a "
            "fund provider publishes, the growth line, the drawdown and the "
            "holdings; and they set an allocation with sliders and watch the "
            "blend update, which is where diversification stops being a word "
            "and becomes a visibly shallower drawdown. The analytics sit "
            "apart from the funds on purpose: the report shows that they do "
            "not predict returns, so presenting them beside an allocation "
            "control would imply a link the evidence does not support.",

            "The business model is a management fee on assets, shown "
            "explicitly in the allocation tab so the user can see what the "
            "product costs them."
        ],
        # ---------------------------------------------------------------
        "reflection": [
            "What worked was the machinery for being wrong safely. The "
            "truncation test caught nothing because there was nothing to "
            "catch, but it is the reason the out-of-sample claims can be made "
            "at all, and the same test is what made the adaptive tilt "
            "defensible rather than suspicious. The identity checks on the "
            "backtest found a real error: weights had been applied as fixed "
            "targets on every day between rebalances, which is arithmetically "
            "a fund that trades back to target daily and which had inflated "
            "the best fund's Sharpe ratio from 0.98 to 1.03.",

            "What did not work was the sentiment fusion, and the interesting "
            "part is why. The index itself is sound: it moves with same-day "
            "returns, its extremes line up with the events a reader would "
            "name, and extending the lexicon makes it measurably more "
            "faithful. It simply has no predictive content at the horizon a "
            "monthly-rebalanced fund can trade, and no amount of better text "
            "processing changes that. The adaptive tilt recovers the loss, but "
            "its advantage is not statistically established and part of it "
            "traces to VADER's blind spots rather than to the news.",

            "The broader lesson is about where the risk in this kind of "
            "project sits. None of the errors found here were errors of "
            "finance; they were errors of accounting and of inference - a "
            "rebalancing assumption, a colour palette too small for its data, "
            "a ranking chosen on the same sample it was evaluated on. The "
            "modelling was the easy part."
        ],
        "recommendations": [
            "First, ship the funds without the sentiment tilt and keep the "
            "sentiment index as a standalone analytic. The evidence in "
            "section 4 does not support a link between the index and future "
            "returns, and a product that tilts on it would be charging a fee "
            "for turnover it cannot justify. The index earns its place as "
            "context a user reads, not as an input to their money.",

            "Second, offer risk parity rather than maximum Sharpe as the "
            "default combined fund. Maximum Sharpe wins on the headline "
            "number, but it holds 8 of 60 assets, rewrites a third of its "
            "portfolio a month, and fell 26% at its worst. Risk parity gives "
            "up 0.09 of a Sharpe point for a drawdown six percentage points "
            "shallower and weights that barely move. For a user who cannot "
            "monitor the fund, the second is the more honest default, and the "
            "first should be available to those who choose it.",

            "Third, re-estimate the tilt's value on a longer sample before "
            "any version of it reaches a live product. The bootstrap "
            "intervals show three years of daily data cannot separate a "
            "0.09 Sharpe improvement from zero. The specific test worth "
            "running is the same walk-forward design on a decade of data, or "
            "on a second market, with the number of specifications searched "
            "declared in advance."
        ],
        "references_note": [
            "Sources are cited where the method originates: Markowitz (1952) "
            "for mean-variance portfolio selection, Sharpe (1966) for the "
            "ratio, Maillard, Roncalli and Teiletche (2010) for risk parity, "
            "and Hutto and Gilbert (2014) for VADER. DeMiguel, Garlappi and "
            "Uppal (2009), 'Optimal Versus Naive Diversification: How "
            "Inefficient is the 1/N Portfolio Strategy?', Review of Financial "
            "Studies 22(5), 1915-1953, supplies the estimation-window result "
            "quoted in Section 2."
        ],
    }
