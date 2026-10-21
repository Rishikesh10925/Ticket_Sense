"""Plain SVG figures for the results chapter (Roadmap Week 10: "produce all figures").

No plotting library: the figures are simple line and bar charts, and writing SVG
directly keeps the evaluation package free of a heavy dependency and makes the output
byte-for-byte reproducible.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 560, 380
LEFT, RIGHT, TOP, BOTTOM = 60, 20, 40, 50
COLOURS = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#4b5563", "#ca8a04")


def _x(v: float, lo: float, hi: float) -> float:
    return LEFT + (v - lo) / (hi - lo or 1) * (W - LEFT - RIGHT)


def _y(v: float, lo: float, hi: float) -> float:
    return H - BOTTOM - (v - lo) / (hi - lo or 1) * (H - TOP - BOTTOM)


def _frame(title: str, xlabel: str, ylabel: str, x_range: tuple[float, float], y_range: tuple[float, float]) -> list[str]:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           'font-family="sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="{W / 2}" y="22" text-anchor="middle" font-size="14" font-weight="bold">{escape(title)}</text>']
    for i in range(6):
        fx = x_range[0] + i * (x_range[1] - x_range[0]) / 5
        fy = y_range[0] + i * (y_range[1] - y_range[0]) / 5
        x, y = _x(fx, *x_range), _y(fy, *y_range)
        out += [f'<line x1="{x:.1f}" y1="{TOP}" x2="{x:.1f}" y2="{H - BOTTOM}" stroke="#e5e7eb"/>',
                f'<text x="{x:.1f}" y="{H - BOTTOM + 16}" text-anchor="middle">{fx:.2f}</text>',
                f'<line x1="{LEFT}" y1="{y:.1f}" x2="{W - RIGHT}" y2="{y:.1f}" stroke="#e5e7eb"/>',
                f'<text x="{LEFT - 6}" y="{y + 4:.1f}" text-anchor="end">{fy:.2f}</text>']
    out += [f'<rect x="{LEFT}" y="{TOP}" width="{W - LEFT - RIGHT}" height="{H - TOP - BOTTOM}" fill="none" stroke="#6b7280"/>',
            f'<text x="{(LEFT + W - RIGHT) / 2}" y="{H - 12}" text-anchor="middle">{escape(xlabel)}</text>',
            f'<text x="16" y="{(TOP + H - BOTTOM) / 2}" text-anchor="middle" '
            f'transform="rotate(-90 16 {(TOP + H - BOTTOM) / 2})">{escape(ylabel)}</text>']
    return out


def _legend(names: Sequence[str]) -> list[str]:
    out = []
    for i, name in enumerate(names):
        y = TOP + 14 + i * 16
        out += [f'<line x1="{LEFT + 10}" y1="{y - 4}" x2="{LEFT + 30}" y2="{y - 4}" stroke="{COLOURS[i % len(COLOURS)]}" stroke-width="2"/>',
                f'<text x="{LEFT + 36}" y="{y}">{escape(name)}</text>']
    return out


def line_chart(path: Path, title: str, xlabel: str, ylabel: str, series: dict[str, tuple[Sequence[float], Sequence[float]]],
               x_range: tuple[float, float] = (0.0, 1.0), y_range: tuple[float, float] | None = None,
               diagonal: bool = False) -> Path:
    """One polyline per series: {name: (xs, ys)}."""
    ys_all = [y for _, ys in series.values() for y in ys]
    y_range = y_range or (0.0, max(ys_all + [0.01]) * 1.1)
    out = _frame(title, xlabel, ylabel, x_range, y_range)
    if diagonal:
        out.append(f'<line x1="{_x(x_range[0], *x_range)}" y1="{_y(y_range[0], *y_range)}" '
                   f'x2="{_x(x_range[1], *x_range)}" y2="{_y(y_range[1], *y_range)}" stroke="#9ca3af" stroke-dasharray="4 4"/>')
    for i, (xs, ys) in enumerate(series.values()):
        pts = " ".join(f"{_x(x, *x_range):.1f},{_y(y, *y_range):.1f}" for x, y in zip(xs, ys) if y is not None)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{COLOURS[i % len(COLOURS)]}" stroke-width="2"/>')
    out += _legend(list(series))
    out.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def bar_chart(path: Path, title: str, xlabel: str, ylabel: str, edges: Sequence[float], counts: Sequence[int],
              marker: float | None = None) -> Path:
    """Histogram from bin edges and counts, with an optional vertical marker (e.g. alpha)."""
    x_range = (float(edges[0]), float(edges[-1]))
    y_range = (0.0, max(list(counts) + [1]) * 1.1)
    out = _frame(title, xlabel, ylabel, x_range, y_range)
    for lo, hi, c in zip(edges[:-1], edges[1:], counts):
        x0, x1 = _x(lo, *x_range), _x(hi, *x_range)
        y = _y(c, *y_range)
        out.append(f'<rect x="{x0 + 1:.1f}" y="{y:.1f}" width="{max(x1 - x0 - 2, 1):.1f}" '
                   f'height="{_y(0, *y_range) - y:.1f}" fill="{COLOURS[0]}"/>')
    if marker is not None:
        x = _x(marker, *x_range)
        out += [f'<line x1="{x:.1f}" y1="{TOP}" x2="{x:.1f}" y2="{H - BOTTOM}" stroke="{COLOURS[1]}" stroke-dasharray="6 3"/>',
                f'<text x="{x + 4:.1f}" y="{TOP + 14}" fill="{COLOURS[1]}">{marker:g}</text>']
    out.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
