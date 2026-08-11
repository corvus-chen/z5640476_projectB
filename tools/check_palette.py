"""Measure a categorical palette: pairwise CIE Lab separation, normal + CVD.

Reports the minimum deltaE (CIE76) over every colour pair, under normal
vision and under simulated deuteranopia and protanopia (Vienot et al. 1999).
A categorical palette needs every pair separated, not just adjacent ones,
because a stacked chart can place any two bands next to each other.
"""
import itertools
import sys

import numpy as np


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_xyz(rgb):
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    return m @ rgb


def xyz_to_lab(xyz):
    white = np.array([0.95047, 1.0, 1.08883])
    t = xyz / white
    f = np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def to_lab(hexcode):
    return xyz_to_lab(linear_to_xyz(srgb_to_linear(hex_to_rgb(hexcode))))


# Vienot/Brettel dichromat simulation in linear RGB.
_DEUTER = np.array([[0.625, 0.375, 0.0],
                    [0.700, 0.300, 0.0],
                    [0.0, 0.300, 0.700]])
_PROTAN = np.array([[0.567, 0.433, 0.0],
                    [0.558, 0.442, 0.0],
                    [0.0, 0.242, 0.758]])


def simulate(hexcode, matrix):
    lin = srgb_to_linear(hex_to_rgb(hexcode))
    sim = np.clip(matrix @ lin, 0, 1)
    return xyz_to_lab(linear_to_xyz(sim))


def report(palette, names=None, threshold=15.0):
    names = names or [f"c{i}" for i in range(len(palette))]
    modes = {
        "normal": lambda h: to_lab(h),
        "deuteranopia": lambda h: simulate(h, _DEUTER),
        "protanopia": lambda h: simulate(h, _PROTAN),
    }
    worst_overall = (1e9, None, None)
    ok = True
    for mode, fn in modes.items():
        labs = [fn(h) for h in palette]
        worst, pair = 1e9, None
        for i, j in itertools.combinations(range(len(palette)), 2):
            d = float(np.linalg.norm(labs[i] - labs[j]))
            if d < worst:
                worst, pair = d, (names[i], names[j])
        flag = "OK  " if worst >= threshold else "FAIL"
        if worst < threshold:
            ok = False
        print(f"  {flag} {mode:13s} min deltaE {worst:5.1f}  "
              f"closest pair: {pair[0]} / {pair[1]}")
        if worst < worst_overall[0]:
            worst_overall = (worst, mode, pair)
    print(f"  -> worst case {worst_overall[0]:.1f} "
          f"({worst_overall[1]}, {worst_overall[2][0]}/{worst_overall[2][1]})")
    return ok, worst_overall[0]


if __name__ == "__main__":
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from src import figstyle as fs  # noqa: E402

    names = ["blue", "green", "amber", "darkgreen", "violet", "rose",
             "deepred", "paleblue", "khaki", "lavender", "teal", "peach"]

    print(f"Brand palette ({len(fs.SERIES)} slots):")
    ok_brand, _ = report(fs.SERIES, names[:len(fs.SERIES)])

    print(f"\nExtended palette ({len(fs.SERIES_EXTENDED)} slots):")
    ok_ext, worst = report(fs.SERIES_EXTENDED, names[:len(fs.SERIES_EXTENDED)])

    if sys.argv[1:]:
        print(f"\nCandidate palette ({len(sys.argv[1:])} slots):")
        report(sys.argv[1:])

    print()
    if ok_brand and ok_ext:
        print(f"PASS - every pair separated by at least deltaE {worst:.1f} "
              "in all three vision models.")
    else:
        print("FAIL - at least one pair is too close; re-run the search.")
        sys.exit(1)
