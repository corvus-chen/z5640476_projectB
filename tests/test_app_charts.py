"""Guard the app against colour-length crashes.

Streamlit requires a chart's colour list to match its column count exactly.
Every chart whose series count comes from a user selection therefore breaks
the moment the selection outgrows the palette slice feeding it - which is
exactly what happened three times here: six funds charted, six funds blended,
and six sectors plotted each raised StreamlitColorLengthError in a build whose
default selections all sat at five or fewer.

Defaults will never catch that. These tests max out every selection.

    python -m pytest tests/test_app_charts.py
"""
import pathlib
import sys

from streamlit.testing.v1 import AppTest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

APP = str(ROOT / "streamlit_app.py")
TIMEOUT = 240


def _run(mutate=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    if mutate is not None:
        mutate(at)
        at.run()
    return at


def _assert_clean(at: AppTest, what: str) -> None:
    assert not at.exception, \
        f"{what}: {[str(e.value)[:200] for e in at.exception]}"


def test_default_render():
    _assert_clean(_run(), "default render")


def test_every_selection_maxed():
    """The case the defaults hide: every multiselect at full length."""
    def mutate(at):
        for ms in at.multiselect:
            ms.set_value(list(ms.options))
    at = _run(mutate)
    _assert_clean(at, "all selections maxed")


def test_every_selection_empty():
    """The other end: nothing selected must show guidance, not traceback."""
    def mutate(at):
        for ms in at.multiselect:
            ms.set_value([])
    _assert_clean(_run(mutate), "all selections empty")


def test_each_multiselect_individually_maxed():
    for i in range(len(_run().multiselect)):
        def mutate(at, i=i):
            at.multiselect[i].set_value(list(at.multiselect[i].options))
        _assert_clean(_run(mutate), f"multiselect {i} maxed")


def test_every_fund_fact_sheet():
    """Each family annualises differently and has a different sector mix."""
    base = _run()
    for fund in base.selectbox[0].options:
        def mutate(at, fund=fund):
            at.selectbox[0].select(fund)
        _assert_clean(_run(mutate), f"fact sheet for {fund}")


def test_palette_covers_every_chart_series():
    """The app palette must hold at least as many slots as the widest chart."""
    from src import figstyle as fs
    import streamlit_app as app

    assert app.SERIES_EXTENDED == fs.SERIES_EXTENDED, \
        "app palette has drifted from the figure design system"

    at = _run()
    widest = max(len(ms.options) for ms in at.multiselect)
    assert widest <= len(app.SERIES_EXTENDED), \
        (f"a selection can reach {widest} series but the palette has only "
         f"{len(app.SERIES_EXTENDED)} slots")


if __name__ == "__main__":
    test_default_render()
    test_every_selection_maxed()
    test_every_selection_empty()
    test_each_multiselect_individually_maxed()
    test_every_fund_fact_sheet()
    test_palette_covers_every_chart_series()
    print("app chart tests passed")
