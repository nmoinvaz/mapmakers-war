#!/usr/bin/env python3
"""The loading bar's steps on each run, as stacked bars grouped by build, from navigation to the bar's end.

python3 scripts/boot_steps.py review/boot-steps-160.json out.svg

The data names each build's runs as the times, in ms, the bar reached 0.62, 0.7, 0.84, 0.92 and 1.0.
"""
import json
import sys

from data_graphs import SERIES, Svg, axes, better_hint, callout, caption, footnote, host_specs, legend, segment

MARKS = ["0.62", "0.7", "0.84", "0.92", "1.0"]
STEPS = ["page and scripts", "set-up", "title map", "compile waits", "the rest"]
# The two steps of least interest share the neutral slot.
COLORS = [SERIES[0], SERIES[-1], SERIES[1], SERIES[2], SERIES[-1]]
LABEL_INK = ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"]


def spans(run):
    t = [0] + [run[m] for m in MARKS]
    return [(t[i] / 1000, t[i + 1] / 1000) for i in range(len(STEPS))]


def main(src, out):
    data = json.load(open(src))
    builds = data["builds"]
    rows = [(b["name"], i, r) for b in builds for i, r in enumerate(b["runs"])]
    n = len(rows)
    end = max(r["1.0"] for _, _, r in rows) / 1000

    svg = Svg(860)
    top = caption(svg, 16, 22, "Loading bar's steps on a cold start, each run",
                  "lower is better · " + data["note"])
    x, y, w, h = 150, top + 10, 600, 30 * n
    labels = [f"{name}, run {i + 1}" for name, i, _ in rows]
    xmap, ymap = axes(svg, x, y, w, h, (0, max(5, int(end) + 1)), (-0.5, n - 0.5), "time from navigation (s)", "run",
                      xfmt=lambda v: f"{v:g}", yfmt=lambda v: labels[n - 1 - int(v)] if 0 <= v < n else "")
    better_hint(svg, x, y, w, h, where="axis", label="faster", reverse=True)
    # The axis labels round ticks only, so each row without one is labeled here.
    for v in range(n):
        if v not in ymap.ticks():
            svg.text(x - 6, ymap(v) + 4, labels[n - 1 - v], size=11, anchor="end", tabular=True)
    bh = 20
    for ri, (name, i, run) in enumerate(rows):
        cy = ymap(n - 1 - ri) - bh / 2
        for si, (a, b) in enumerate(spans(run)):
            segment(svg, xmap(a), xmap(b), cy, bh, COLORS[si], f"{name} run {i + 1}, {STEPS[si]}: {b - a:.2f} s",
                    label=[f"{b - a:.1f}"], ink=LABEL_INK[si])
    legend(svg, x + w, top - 6, [(s, COLORS[i]) for i, s in enumerate(STEPS) if s != "the rest"])

    # Each build's mean time to the bar's end, on its last run.
    means = [sum(r["1.0"] for r in b["runs"]) / len(b["runs"]) / 1000 for b in builds]
    for bi, b in enumerate(builds):
        ri = max(k for k, (name, _, _) in enumerate(rows) if name == b["name"])
        callout(svg, xmap(rows[ri][2]["1.0"] / 1000), ymap(n - 1 - ri), f"mean {means[bi]:.2f} s", dx=40, dy=0)

    height = footnote(svg, [f"{b['name']}: {len(b['runs'])} runs" for b in builds],
                      host_specs() + ", in a Fedora 43 container", [data["warn"]], y + h + 44,
                      "https://github.com/nmoinvaz/mapmakers-war")
    open(out, "w").write(svg.finish(height))

    print(f"{'run':<18}" + "".join(f"{s:>18}" for s in STEPS) + f"{'end':>8}")
    for name, i, run in rows:
        print(f"{name + ' ' + str(i + 1):<18}" + "".join(f"{b - a:>17.2f}s" for a, b in spans(run)) + f"{run['1.0'] / 1000:>7.2f}s")
    for b, m in zip(builds, means):
        print(f"{b['name']:<18} mean end {m:.2f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
