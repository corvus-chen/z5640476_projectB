---
name: check-exhibit
description: Check a figure or table against the project's self-contained-exhibit standard and design system before it goes in the report or the app. Use after generating or changing any exhibit.
---

# Check an exhibit

Open the rendered PNG and look at it. Reading the plotting code does not
catch collisions, colour clashes, or a canvas that has burst its width - all
three have shipped here after the code looked correct.

## Self-contained

- Title states the finding, not the variable name.
- Subtitle carries units, the sample period, and how to read the chart.
- Both axes labelled with units.
- Source footer present.
- Could a reader who has not read the report understand it alone?

## Design system

- Colours come from `figstyle.SERIES` / `series_colours(n)`, never cycled.
  Two categories sharing a hue is a defect, not a compromise.
- If the chart needs more than 12 categories, pool the smallest - do not
  extend the palette without re-running `tools/check_palette.py`.
- Direct labels rather than a legend where the series can be labelled at their
  end points.
- Multi-panel charts share their scale; only the leftmost carries tick labels.

## Layout traps that have actually happened here

- Direct labels overlapping when two series end close together - use
  `_label_offsets`.
- A legend printed on top of the x-axis label - anchor it lower, or use a
  figure-level legend.
- Prose appended to the source footer: footers never wrap, so a long one
  widens the canvas past A4. Put explanation in the subtitle instead.
- Panel titles colliding with a subtitle that wrapped to three lines.
- A daily series too noisy to read - smooth for the exhibit and say the window
  in the subtitle, keeping the daily data in the CSV.

## Width

Check the rendered pixel width. At 300 dpi an A4-ready figure is about 1890 px
and should not exceed roughly 2400. Anything wider will be shrunk in Word and
the type will be unreadable.

## Output

Say what you looked at, what you changed, and paste the final pixel size.
