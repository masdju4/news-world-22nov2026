#!/usr/bin/env python3
"""Draw the make.fun entry image: one frame summing up the world news of
Sunday 22 November 2026. Standard library + Pillow only, offline, deterministic.

Run:  python3 draw_news.py [outfile]
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W = H = 1024

FD = "/usr/share/fonts/truetype/dejavu"
FB = os.path.join(FD, "DejaVuSans-Bold.ttf")
FR = os.path.join(FD, "DejaVuSans.ttf")
FN = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

INK = (233, 240, 250)
DIM = (150, 166, 190)
BG = (9, 14, 24)
CARD = (20, 29, 46)
CARD2 = (16, 24, 38)
RULE = (47, 63, 88)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, maxw: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paste_center(img: Image.Image, box, text: str, fnt, fill, maxw=None):
    """Draw text centred horizontally in box=(x0,y0,x1,y1), top-aligned at y0."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, _ = box
    lines = wrap(d, text, fnt, maxw or (x1 - x0))
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=fnt)
        d.text((x0 + (x1 - x0 - tw) / 2, y0 + i * (fnt.size + 5)), ln, font=fnt, fill=fill)
    return y0 + len(lines) * (fnt.size + 5)


# ---------------------------------------------------------------- icon helpers
def ic_ukraine(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Missile arcs over a skyline with a blast."""
    for k, r in enumerate((s * 0.95, s * 0.70)):
        d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=c[0], width=5)
    for i, (dx, h) in enumerate(((-2.2, 0.55), (-1.35, 0.85), (-0.45, 0.65), (0.5, 1.0), (1.4, 0.7), (2.2, 0.5))):
        x = cx + dx * s * 0.42
        hh = h * s * 0.72
        d.rectangle([x - s * 0.16, cy + s * 0.75 - hh, x + s * 0.16, cy + s * 0.75], fill=c[1])
    # blast
    bx, by, br = cx + s * 0.30, cy + s * 0.10, s * 0.30
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=c[2])
    d.ellipse([bx - br * 0.45, by - br * 0.45, bx + br * 0.45, by + br * 0.45], fill=(255, 236, 190))


def ic_climate(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Globe with latitude lines and a rising heat bar."""
    r = s * 0.80
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c[0], width=5)
    for f in (0.38, 0.72):
        d.ellipse([cx - r, cy - r * f, cx + r, cy + r * f], outline=c[0], width=3)
    d.line([cx - r, cy, cx + r, cy], fill=c[0], width=3)
    d.line([cx, cy - r, cx, cy + r], fill=c[0], width=3)
    # heat bars
    bx = cx + r * 0.92
    for i, hh in enumerate((0.45, 0.75, 1.15)):
        x = bx + i * s * 0.20
        d.rectangle([x, cy + r * 0.85 - s * hh, x + s * 0.12, cy + r * 0.85], fill=c[1] if i < 2 else c[2])


def ic_protest(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Crowd with placards."""
    import random

    rnd = random.Random(7)
    base = cy + s * 0.85
    for i in range(11):
        x = cx - s * 0.95 + i * (s * 1.9 / 10)
        hh = s * rnd.uniform(0.34, 0.50)
        d.ellipse([x - s * 0.085, base - hh - s * 0.17, x + s * 0.085, base - hh], fill=c[1])
        d.rectangle([x - s * 0.105, base - hh, x + s * 0.105, base], fill=c[1])
    for x, dy, col in ((cx - s * 0.62, 0.86, c[2]), (cx + s * 0.10, 1.05, c[0]), (cx + s * 0.72, 0.80, c[2])):
        top = base - s * dy - s * 0.40
        d.line([x, base - s * 0.30, x, top + s * 0.26], fill=c[3], width=4)
        d.rectangle([x - s * 0.24, top, x + s * 0.24, top + s * 0.26], fill=col)


def ic_cartel(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Handcuffs over a two-star badge."""
    r = s * 0.30
    for dx in (-0.52, 0.52):
        x = cx + dx * s
        d.ellipse([x - r, cy - r, x + r, cy + r], outline=c[0], width=7)
    d.line([cx - s * 0.52 + r, cy, cx + s * 0.52 - r, cy], fill=c[0], width=7)
    d.line([cx - s * 0.30, cy - s * 0.62, cx + s * 0.30, cy - s * 0.62], fill=c[1], width=6)
    for i, dx in enumerate((-0.30, 0.0, 0.30)):
        x = cx + dx * s
        d.regular_polygon((x, cy + s * 0.62, s * 0.13), n_sides=5, rotation=-90, fill=c[2])


def ic_market(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Falling candlesticks and an arrow."""
    pts = []
    for i in range(7):
        x = cx - s * 0.95 + i * (s * 1.9 / 6)
        y = cy - s * 0.55 + (i ** 1.5) * s * 0.115
        pts.append((x, y))
    d.line(pts, fill=c[2], width=6, joint="curve")
    ax, ay = pts[-1]
    d.polygon([(ax + s * 0.02, ay + s * 0.42), (ax - s * 0.24, ay + s * 0.02), (ax + s * 0.16, ay - s * 0.04)], fill=c[2])
    for x, y in pts[:5]:
        d.rectangle([x - s * 0.06, y - s * 0.14, x + s * 0.06, y + s * 0.14], fill=c[1])


def ic_boat(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, c: tuple):
    """Overturned hull on waves."""
    hull = [(cx - s * 0.95, cy + s * 0.10), (cx + s * 0.95, cy + s * 0.10),
            (cx + s * 0.62, cy + s * 0.52), (cx - s * 0.62, cy + s * 0.52)]
    d.polygon(hull, fill=c[0])
    d.rectangle([cx - s * 0.30, cy + s * 0.06, cx + s * 0.30, cy + s * 0.12], fill=c[1])
    for k in range(3):
        y = cy + s * (0.66 + 0.16 * k)
        x0 = cx - s * 0.95
        step = s * 0.24
        x = x0
        while x < cx + s * 0.95:
            d.arc([x, y - s * 0.10, x + step * 2, y + s * 0.10], 0, 180, fill=c[2], width=4)
            x += step * 2


# ---------------------------------------------------------------------- content
STORIES = [
    ("WAR IN EUROPE", "KYIV HIT", "Russian drones and missiles pound the Kyiv region; rescuers dig for survivors near Dymer.", (255, 176, 66), ic_ukraine),
    ("CLIMATE", "COP31 IN DOUBT", "A new draft lands in Antalya; the EU rejects it and the summit runs past its deadline.", (94, 214, 165), ic_climate),
    ("COST OF LIVING", "EUROPE MARCHES", "Sixth weekend of protests in France, Spain and Portugal over wages, schools and prices.", (255, 122, 122), ic_protest),
    ("CRIME", "CARTEL BOSS HELD", "Mexico detains Fausto Isidro Meza Flores in Sinaloa with US help; he was on the FBI top ten.", (126, 184, 255), ic_cartel),
    ("MARKETS", "NVIDIA SELL-OFF", "The AI trade unwinds: Nvidia slides again as investors question its accounting.", (255, 208, 96), ic_market),
    ("AFRICA", "BOAT CAPSIZES", "At least 24 die as a boat carrying mourners to a funeral capsizes in Nigeria.", (178, 158, 255), ic_boat),
]

MX, GAP = 30, 18
TOP = 196
CW = (W - 2 * MX - GAP) // 2
CH = (H - TOP - MX - 2 * GAP) // 3

ICON_CY = 62          # icon centre offset inside a card
RULE_Y = 110
KICK_Y = 118
HEAD_Y = 138
CAP_Y = 176


def draw() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # masthead
    d.rectangle([0, 0, W, 6], fill=(255, 176, 66))
    paste_center(img, (MX, 24, W - MX, 88), "22 NOVEMBER 2026", font(FB, 56), INK)
    paste_center(img, (MX, 94, W - MX, 124), "SUNDAY  ·  THE WORLD'S NEWS IN ONE FRAME", font(FR, 23), DIM)
    d.line([MX, 148, W - MX, 148], fill=RULE, width=2)
    paste_center(img, (MX, 156, W - MX, 182), "KYIV  ·  ANTALYA  ·  PARIS  ·  CULIACÁN  ·  WALL STREET  ·  NIGERIA", font(FM, 15), (108, 128, 156))

    for i, (kicker, head, cap, accent, icon) in enumerate(STORIES):
        col, row = i % 2, i // 2
        x0 = MX + col * (CW + GAP)
        y0 = TOP + row * (CH + GAP)
        x1, y1 = x0 + CW, y0 + CH
        d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=CARD if (i % 2 == 0) else CARD2, outline=RULE, width=2)
        d.rectangle([x0, y0 + 16, x0 + 6, y1 - 16], fill=accent)

        icon(
            d, x0 + CW * 0.5, y0 + ICON_CY, 40,
            (accent, (236, 242, 252), accent, (196, 208, 226)),
        )
        d.line([x0 + 24, y0 + RULE_Y, x1 - 24, y0 + RULE_Y], fill=RULE, width=1)

        paste_center(img, (x0 + 20, y0 + KICK_Y, x1 - 20, y0 + KICK_Y + 18), kicker, font(FM, 14), accent)
        paste_center(img, (x0 + 20, y0 + HEAD_Y, x1 - 20, y0 + HEAD_Y + 34), head, font(FB, 26), INK)
        paste_center(img, (x0 + 20, y0 + CAP_Y, x1 - 20, y1 - 12), cap, font(FR, 17), DIM)

    # footer
    paste_center(img, (MX, H - 26, W - MX, H - 10), "make.fun  ·  one picture, one day", font(FR, 14), (86, 104, 130))
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    im = draw()
    im.save(out, "PNG", optimize=True)
    print(f"wrote {out} {im.size[0]}x{im.size[1]} {os.path.getsize(out)} bytes")