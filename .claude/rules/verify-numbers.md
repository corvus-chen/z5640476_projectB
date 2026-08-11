# Rule: every number is traceable, or it does not go in

The assistant computes; I interpret. That split only works if I can re-run
anything it hands me.

## Never

- Never state a statistic from memory, including one produced earlier in the
  same session. Re-run it. Recalled numbers have already been wrong here: a
  docstring claimed 30 dropped headlines when the true count was 6.
- Never invent a citation, a source, an author, or a year.
- Never quote a figure caption's number without checking it against the
  artifact the figure was built from.
- Never present a number whose provenance you cannot name.

## Always

- Show the working for any number that enters the report: which file, which
  function, which sample.
- When a result looks wrong, check the arithmetic before changing the code.
  The crypto fund showing a positive Sharpe and a negative annualised return
  was volatility drag, not a bug - the fix was reporting both means, not
  editing the formula.
- Flag what you cannot verify instead of stating it confidently. Say "I have
  not checked this" in those words.
- Remind me to check the output before I rely on it.

## The check I want run on any surprising result

State it as a prediction first ("if this is right, X should also be true"),
then test X. A single-asset portfolio must reproduce that asset exactly; a
truncated backtest must not change earlier values; weights must sum to one.
Cheap identity checks catch more than re-reading the code does.
