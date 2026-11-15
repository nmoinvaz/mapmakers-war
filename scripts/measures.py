#!/usr/bin/env python3
"""A few measures before and after a change, as a dot for each run on each measure's row.

python3 scripts/measures.py review/frame-cost-162.json out.svg

The data gives a title, a note, an axis label, the rows' names, and each build's runs as one value per row.
"""
import json
import sys

from data_graphs import (SERIES, SHAPES, Svg, axes, better_hint, callout, caption, footnote, host_specs,
                         legend, marker, nice_step, pct)


def main(src, out):
    data = json.load(open(src))
    rows, builds = data["rows"], data["builds"]
    # The build before takes the neutral last slot, as the series of least interest.
    colors = [SERIES[-1], SERIES[0]] if len(builds) == 2 else SERIES[:len(builds)]
    order = list(reversed(range(len(builds)))) if len(builds) == 2 else range(len(builds))
    hi = max(v for b in builds for run in b["runs"] for v in run)
    step = nice_step(hi, 5)
    top_x = step * (int(hi / step) + 1)

    svg = Svg(860)
    top = caption(svg, 16, 22, data["title"], "lower is better · " + data["note"])
    n = len(rows)
    x, y, w, h = 230, top + 6, 520, 40 * n + 16
    xmap, ymap = axes(svg, x, y, w, h, (0, top_x), (-0.9, n - 0.5), data["unit"], "measure",
                      xfmt=lambda v: f"{v:g}", yfmt=lambda v: rows[n - 1 - int(v)] if 0 <= v < n and v == int(v) else "")
    better_hint(svg, x, y, w, h, where="axis", label="faster", reverse=True)
    for v in range(n):
        if v not in ymap.ticks():
            svg.text(x - 6, ymap(v) + 4, rows[n - 1 - v], size=11, anchor="end", tabular=True)

    # Each build a little above or below the row's middle, and its runs a few pixels apart, so x stays the value.
    off = lambda bi: (bi - (len(builds) - 1) / 2) * 12
    for bi in order:
        b = builds[bi]
        for ri in range(n):
            for k, run in enumerate(b["runs"]):
                dy = (k - (len(b["runs"]) - 1) / 2) * 4
                marker(svg, SHAPES[bi], xmap(run[ri]), ymap(n - 1 - ri) + off(bi) + dy, colors[bi],
                       f"{b['name']} run {k + 1}, {rows[ri]}: {run[ri]:g}")
    legend(svg, x + w, top - 12, [(b["name"], colors[i]) for i, b in enumerate(builds)])

    # The change in each row's mean, beside the later build's points.
    means = [[sum(run[ri] for run in b["runs"]) / len(b["runs"]) for ri in range(n)] for b in builds]
    for ri in range(n):
        if len(builds) == 2 and ri in data.get("callouts", range(n)):
            callout(svg, xmap(means[1][ri]), ymap(n - 1 - ri) + off(1), pct(means[1][ri], means[0][ri]), dx=30, dy=16)

    height = footnote(svg, [b["source"] for b in builds], host_specs(), [data["warn"]] if data.get("warn") else [],
                      y + h + 44, "https://github.com/nmoinvaz/mapmakers-war")
    open(out, "w").write(svg.finish(height))

    print(f"{'measure':<34}" + "".join(f"{b['name']:>14}" for b in builds) + f"{'change':>10}")
    for ri, r in enumerate(rows):
        print(f"{r:<34}" + "".join(f"{means[bi][ri]:>14.2f}" for bi in range(len(builds)))
              + (f"{pct(means[1][ri], means[0][ri]):>10}" if len(builds) == 2 else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
