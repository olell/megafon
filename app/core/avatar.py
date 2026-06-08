"""Deterministic, self-contained user avatars.

A smooth "blob" identicon: a vertically-mirrored grid of dots that are merged
into one organic shape with an SVG gooey filter (Gaussian blur + alpha
contrast), then filled with a hash-derived gradient on a tinted backdrop. Pure
stdlib (no fonts, no image assets, no third-party deps) so it works fully
offline and never depends on the host system. Because it only ever emits
coloured shapes it can't surface anything culturally loaded — random seeds are
always safe. Colours adapt to light/dark mode (the caller passes `dark`).
"""

import functools
import hashlib

# Visual tuning — change these to re-style every avatar at once.
SIZE = 80  # SVG viewBox edge (px); the frontend scales it down.
GRID = 5  # cells per side
_COLS = GRID // 2 + 1  # unique left columns; the rest are mirrored
_PAD_FRAC = 0.16  # padding around the grid, as a fraction of SIZE
_THICK_FRAC = 1.0  # tube thickness, as a fraction of a cell
_BLUR_FRAC = 0.14  # gooey blur radius, as a fraction of a cell (gentle: just fillets)


def _digest(seed: str) -> bytes:
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """h in [0, 360); s, l in [0, 1] -> '#rrggbb'."""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return "#{:02x}{:02x}{:02x}".format(
        round((r + m) * 255), round((g + m) * 255), round((b + m) * 255)
    )


def _palette(hue: float, dark: bool) -> tuple[str, str, str]:
    """(background, gradient-top, gradient-bottom). Constrained ranges keep every
    avatar harmonious and legible, brightened for contrast in dark mode."""
    if dark:
        return (
            _hsl_to_hex(hue, 0.32, 0.17),  # deep tinted backdrop
            _hsl_to_hex(hue, 0.72, 0.64),
            _hsl_to_hex(hue, 0.78, 0.50),
        )
    return (
        _hsl_to_hex(hue, 0.45, 0.93),  # pale tinted backdrop
        _hsl_to_hex(hue, 0.68, 0.54),
        _hsl_to_hex(hue, 0.72, 0.40),
    )


@functools.lru_cache(maxsize=4096)
def identicon_svg(seed: str, dark: bool = False, size: int = SIZE) -> str:
    """Deterministic smooth-blob identicon SVG for ``seed`` (e.g. a user id)."""
    d = _digest(seed)
    hue = d[0] / 255 * 360
    bg, fg1, fg2 = _palette(hue, dark)

    # 4 bytes -> 32 bits; we need GRID*_COLS (= 15) to fill the left/centre cells.
    bits = int.from_bytes(d[1:5], "big")

    pad = size * _PAD_FRAC
    cell = (size - 2 * pad) / GRID
    thick = cell * _THICK_FRAC
    half = thick / 2
    blur = cell * _BLUR_FRAC

    # Expand the hashed bits into the full mirrored grid.
    filled = [[False] * GRID for _ in range(GRID)]
    for col in range(_COLS):
        for row in range(GRID):
            if (bits >> (col * GRID + row)) & 1:
                filled[row][col] = True
                filled[row][GRID - 1 - col] = True

    def cx(c: int) -> float:
        return pad + (c + 0.5) * cell

    def cy(r: int) -> float:
        return pad + (r + 0.5) * cell

    def bar(x: float, y: float, w: float, h: float) -> str:
        # A capsule (fully rounded ends): rx = half the short side.
        return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{half:.2f}"/>'

    # Merge each maximal run of filled cells into ONE rounded bar, so straight
    # stretches have perfectly straight edges (no per-cell scalloping). The
    # horizontal pass covers every filled cell; the vertical pass only adds bars
    # for runs ≥2 to stitch stacked cells together. The gooey filter then fillets
    # the inner corners where bars meet into a smooth, organic blob.
    shapes = []
    for r in range(GRID):
        c = 0
        while c < GRID:
            if filled[r][c]:
                c0 = c
                while c < GRID and filled[r][c]:
                    c += 1
                shapes.append(bar(cx(c0) - half, cy(r) - half, (c - 1 - c0) * cell + thick, thick))
            else:
                c += 1
    for c in range(GRID):
        r = 0
        while r < GRID:
            if filled[r][c]:
                r0 = r
                while r < GRID and filled[r][c]:
                    r += 1
                if r - 1 > r0:  # length ≥ 2
                    shapes.append(bar(cx(c) - half, cy(r0) - half, thick, (r - 1 - r0) * cell + thick))
            else:
                r += 1

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" role="img">'
        f"<defs>"
        f'<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{fg1}"/>'
        f'<stop offset="1" stop-color="{fg2}"/>'
        f"</linearGradient>"
        f'<filter id="goo">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{blur:.2f}" result="b"/>'
        f'<feColorMatrix in="b" mode="matrix" '
        f'values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 14 -5"/>'
        f"</filter>"
        f"</defs>"
        f'<rect width="{size}" height="{size}" fill="{bg}"/>'
        f'<g filter="url(#goo)" fill="url(#g)">{"".join(shapes)}</g>'
        f"</svg>"
    )
