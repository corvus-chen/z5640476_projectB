"""Finance lexicon extension for VADER. (Innovation extension.)

Why this exists, measured rather than assumed: of the 33,033 distinct tokens
in the 146,836 headlines, only 1,831 carry a VADER score, and 49.6% of
headlines score neutral. The gaps are not obscure words - `earnings` appears
11,870 times, `dividend` 6,742, `beat` 2,083, and VADER scores none of them.

Terms were selected by frequency from the headlines themselves (the most
frequent unscored tokens), not from memory, and fall into two groups:

- MISSING: the word carries clear direction in market reporting and VADER has
  no entry at all ("soars", "downgrade", "bankruptcy").
- MIS-SCORED: VADER has an entry, but its general-English sense understates or
  misreads the market sense. An earnings "miss" is a harder negative than
  missing a bus (-0.6); a market "crash" is worse than a car crash (-1.7).

Scores use VADER's own -4 to +4 scale and are deliberately conservative: they
sit inside the range of comparable words already in VADER rather than at the
extremes, because a headline word is weaker evidence than a full sentence.

AMBIGUOUS TERMS ARE DELIBERATELY EXCLUDED. `cut` reads negative for a dividend
and positive for an interest rate; `hike` reverses the same way; `short`,
`high`, `low`, and `top` depend entirely on context ("52-week high" against
"top 5 stocks to buy" - a listicle, not sentiment). Scoring these would add
noise dressed as signal. They are listed in EXCLUDED with the reason.

[HUMAN EDIT REQUIRED: these scores are AI-proposed and need my review before
the report claims them as my own judgment - the brief sanctions the workflow
(Section 5, "extending VADER's lexicon... having your AI agent propose finance
terms and assign them sentiment scores"), but the calls are mine to sign off.]
"""
from __future__ import annotations

# term -> (score, category, rationale)
TERMS: dict[str, tuple[float, str, str]] = {
    # --- earnings and guidance -------------------------------------------
    "beat": (2.2, "missing", "earnings beat - the single strongest routine positive"),
    "beats": (2.2, "missing", "as above, plural/verb form"),
    "miss": (-2.0, "mis-scored", "VADER -0.6 (missing a bus); an earnings miss is harsher"),
    "misses": (-2.0, "mis-scored", "VADER -0.9; same correction"),
    "missed": (-1.9, "mis-scored", "VADER -1.2; same correction"),
    "guidance": (0.0, "excluded-neutral", "direction comes from raise/cut, not the noun"),
    "estimates": (0.0, "excluded-neutral", "neutral noun; the verb beside it carries sign"),

    # --- analyst actions --------------------------------------------------
    "upgrade": (2.3, "missing", "explicit analyst action, unambiguously positive"),
    "upgrades": (2.3, "missing", "as above"),
    "downgrade": (-2.3, "missing", "explicit analyst action, unambiguously negative"),
    "downgrades": (-2.3, "missing", "as above"),
    "outperform": (2.0, "missing", "rating and relative-performance language"),
    "underperform": (-2.0, "missing", "as above, negative side"),

    # --- price direction --------------------------------------------------
    "soar": (2.8, "missing", "large upward move, strong intensity"),
    "soars": (2.8, "missing", "as above"),
    "surge": (2.4, "missing", "large upward move"),
    "surges": (2.4, "missing", "as above"),
    "rally": (1.9, "missing", "sustained upward move"),
    "jump": (1.7, "missing", "moderate upward move"),
    "jumps": (1.7, "missing", "as above"),
    "rise": (1.2, "missing", "mild upward move"),
    "rises": (1.2, "missing", "as above"),
    "higher": (1.3, "missing", "mild upward move; 3,165 occurrences"),
    "gain": (2.4, "already-in-vader", "VADER +2.4 already suits the market sense"),

    "plunge": (-2.8, "missing", "large downward move, mirrors soar"),
    "plunges": (-2.8, "missing", "as above"),
    "tumble": (-2.4, "missing", "large downward move"),
    "tumbles": (-2.4, "missing", "as above"),
    "slump": (-2.2, "missing", "sustained downward move"),
    "sink": (-2.2, "missing", "downward move"),
    "sinks": (-2.2, "missing", "as above; 445 occurrences"),
    "fall": (-1.2, "missing", "mild downward move, mirrors rise"),
    "falls": (-1.2, "missing", "as above"),
    "drops": (-1.3, "missing", "VADER scores 'drop' but not 'drops'"),
    "crash": (-2.9, "mis-scored", "VADER -1.7 (car crash); a market crash is worse"),

    # --- positioning and sentiment words ----------------------------------
    "bullish": (2.1, "missing", "explicit market-direction stance"),
    "bull": (1.3, "missing", "as above, weaker as a noun ('bull market')"),
    "bearish": (-2.1, "missing", "explicit market-direction stance"),
    "bear": (-1.3, "missing", "as above; VADER has no animal-sense entry either"),
    "volatile": (-1.1, "missing", "risk language, mildly negative for investors"),
    "volatility": (-1.0, "missing", "as above"),

    # --- corporate events -------------------------------------------------
    "bankruptcy": (-3.3, "missing", "terminal corporate outcome"),
    "layoffs": (-2.2, "missing", "negative for workers; ambiguous for the share "
                                 "price, scored on the news tone"),
    "recall": (-2.0, "missing", "product failure event"),
    "fraud": (-3.2, "missing", "already implied by VADER's related words, but "
                               "the bare noun is unscored"),
    "probe": (-1.4, "missing", "regulatory investigation, mildly negative"),
    "halt": (-1.5, "missing", "trading halt, negative in a headline"),
    "dividend": (1.1, "missing", "cash return to shareholders; 6,742 occurrences"),
    "buyback": (1.6, "missing", "capital return, read positively"),
}

# Terms left OUT on purpose - each reverses sign with context.
EXCLUDED: dict[str, str] = {
    "cut": "negative for a dividend cut, positive for a rate cut",
    "cuts": "same reversal as 'cut'",
    "hike": "positive for a dividend hike, negative for a rate hike",
    "short": "'short interest' vs 'short seller' vs 'falls short' - no stable sign",
    "high": "'record high' is positive, 'high costs' negative",
    "low": "mirror of 'high'",
    "top": "'tops estimates' is positive, 'top 5 stocks' is a listicle headline",
    "buy": "15,806 occurrences, but nearly all are listicle imperatives "
           "('3 stocks to buy'), which describe the writer, not the company",
    "sell": "mirror of 'buy'",
    "earnings": "11,870 occurrences but purely a topic noun - the sign sits in "
                "the verb beside it, which the entries above now score",
    "revenue": "topic noun, same reasoning as 'earnings'",
    "record": "'record profit' positive, 'record loss' negative",
}


def lexicon() -> dict[str, float]:
    """The finance terms to merge into VADER, excluding the neutral markers."""
    return {term: score for term, (score, category, _) in TERMS.items()
            if category not in {"excluded-neutral", "already-in-vader"}}


def as_table():
    """The lexicon as a DataFrame, for the report appendix and my review."""
    import pandas as pd
    rows = [{"term": t, "score": s, "category": c, "rationale": r}
            for t, (s, c, r) in TERMS.items()]
    return pd.DataFrame(rows).sort_values(["category", "term"])
