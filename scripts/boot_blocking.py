#!/usr/bin/env python3
"""How long the page is held once the loading bar is done, as a dot chart for each build and backend.

python3 scripts/boot_blocking.py review/boot-blocking-155.json out.svg
"""
import json
import sys

from data_graphs import (INK, SERIES, SHAPES, Svg, axes, better_hint, callout, caption, footnote,
                         host_specs, legend, marker, pct)

ROWS = [("swiftshader", "held", "slow card, held after ready"), ("swiftshader", "longest", "slow card, longest freeze"),
        ("swiftshader", "ready", "slow card, time to ready"), ("metal", "held", "Mac GPU, held after ready"),
        ("metal", "ready", "Mac GPU, time to ready")]


def main(src, out):
    data = json.load(open(src))
    series = data["series"]
    # The neutral last slot goes to the build before, the series of least interest.
    colors = SERIES[:len(series) - 1] + [SERIES[-1]]

    svg = Svg(860)
    top = caption(svg, 16, 22, "Main thread held at start-up, once the DEPLOYING bar is done",
                  "lower is better · " + data["note"])
    n = len(ROWS)
    row = lambda i: n - 1 - i
    x, y, w, h = 210, top, 520, 34 * n
    xmap, ymap = axes(svg, x, y, w, h, (50, 30000, "log"), (-0.5, n - 0.5), "time (ms, log)", "measure",
                      xfmt=lambda v: f"{v:,g}", yfmt=lambda v: ROWS[row(int(v))][2])
    better_hint(svg, x, y, w, h, where="axis", label="faster", reverse=True)

    # One point a row for each build, a little above or below the row's middle so none hides another.
    off = lambda si: (si - (len(series) - 1) / 2) * 8
    pts = [[(xmap(s[b][k]), ymap(row(i)) + off(si)) for i, (b, k, _) in enumerate(ROWS)] for si, s in enumerate(series)]
    for si, s in enumerate(series):
        for (b, k, label), (px, py) in zip(ROWS, pts[si]):
            marker(svg, SHAPES[si], px, py, colors[si], f"{s['name']}, {label}: {s[b][k]:,} ms")
    legend(svg, x + w, top - 12, [(s["name"], colors[i]) for i, s in enumerate(series)])

    # The freeze the nephew saw, and what is left of it.
    now, before = series[0], series[-1]
    callout(svg, *pts[-1][0], f"{before['swiftshader']['held'] / 1000:.1f} s held", dx=-40, dy=22)
    callout(svg, *pts[0][0], f"held {pct(now['swiftshader']['held'], before['swiftshader']['held'])}", dx=30, dy=-14)

    ty = y + h + 62
    svg.text(16, ty, "Shader programs made after ready, through the title and 20 s of a skirmish on the Mac GPU: "
             + ", ".join(f"{s['name']} {s['late']}" for s in series), size=11, fill=INK)
    svg.text(16, ty + 18, "Measured on " + data["page"] + ".", size=11)
    height = footnote(svg, [s["source"] for s in series], host_specs(), [data["warn"]], ty + 24,
                      "https://github.com/nmoinvaz/mapmakers-war")
    open(out, "w").write(svg.finish(height))

    # The same numbers as a table.
    print(f"{'build':<8}" + "".join(f"{label:>30}" for _, _, label in ROWS) + f"{'late':>6}")
    for s in series:
        print(f"{s['name']:<8}" + "".join(f"{s[b][k]:>30,}" for b, k, _ in ROWS) + f"{s['late']:>6}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
