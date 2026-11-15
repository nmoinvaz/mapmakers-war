#!/usr/bin/env python3
"""The shader compiling a cold start asks of the graphics driver, as stacked bars by kind of program, per build.

python3 scripts/compile_cost.py review/compile-cost-159.json out.svg [after-commit]
"""
import json
import sys

from data_graphs import (SERIES, Svg, axes, better_hint, callout, caption, footnote, host_specs, legend, pct,
                         segment)

KINDS = ["ink look", "map materials", "the other passes"]
# Text on each fill, chosen for contrast with it.
LABEL_INK = ["#ffffff", "#ffffff", "#1a1a1a"]


def main(src, out, after="now"):
    data = json.load(open(src))
    progs, gone = data["programs"], set(data["gone"])
    builds = [(data["before"], progs), (after, [p for p in progs if p["id"] not in gone])]
    sums = [{k: sum(p["ms"] for p in ps if p["kind"] == k) for k in KINDS} for _, ps in builds]
    counts = [{k: sum(1 for p in ps if p["kind"] == k) for k in KINDS} for _, ps in builds]
    colors = [SERIES[0], SERIES[1], SERIES[-1]]

    svg = Svg(860)
    top = caption(svg, 16, 22, "Shader compiling on a cold start, by kind of program",
                  "lower is better · " + data["note"])
    x, y, w, h = 150, top + 10, 600, 110
    total = [sum(s.values()) for s in sums]
    xmap, ymap = axes(svg, x, y, w, h, (0, 24, ), (-0.5, 1.5), "compile time (s)", "build",
                      xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{builds[1 - int(v)][0]}" if v in (0, 1) else "")
    better_hint(svg, x, y, w, h, where="axis", label="faster", reverse=True)
    bh = 30
    for bi, ((name, ps), s, c) in enumerate(zip(builds, sums, counts)):
        cy = ymap(1 - bi) - bh / 2
        x0 = 0
        for ki, k in enumerate(KINDS):
            x1 = x0 + s[k] / 1000
            segment(svg, xmap(x0), xmap(x1), cy, bh, colors[ki], f"{name}, {k}: {c[k]} programs, {s[k] / 1000:.1f} s",
                    label=[f"{c[k]} × {k}, {s[k] / 1000:.1f} s", f"{c[k]} {k}", f"{s[k] / 1000:.1f} s"], ink=LABEL_INK[ki])
            x0 = x1
    legend(svg, x + w, top - 6, [(k, colors[i]) for i, k in enumerate(KINDS)])
    callout(svg, xmap(total[1] / 1000), ymap(0), f"{total[1] / 1000:.1f} s, {pct(total[1], total[0])}", dx=36, dy=0)

    height = footnote(svg, [f"{n}: {len(ps)} programs" for n, ps in builds], host_specs() + ", in a Fedora 43 container",
                      [data["warn"]],
                      y + h + 44, "https://github.com/nmoinvaz/mapmakers-war")
    open(out, "w").write(svg.finish(height))

    print(f"{'build':<10}" + "".join(f"{k:>22}" for k in KINDS) + f"{'total':>10}")
    for (n, _), s, c in zip(builds, sums, counts):
        print(f"{n:<10}" + "".join(f"{c[k]:>4} programs {s[k] / 1000:>6.1f} s" for k in KINDS) + f"{sum(s.values()) / 1000:>8.1f} s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
