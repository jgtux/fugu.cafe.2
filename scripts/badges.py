"""Generate 88x31 badges for fugu.cafe using the site's own palette.

One espresso set for both themes: on the latte background the badges read
as dark chips, which is how 88x31 buttons always looked anyway.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 88, 31
# espresso surfaces from css/style.css (dark side of light-dark())
BG = (33, 25, 19)       # --surface #211913
EDGE = (58, 45, 35)     # --border #3a2d23
HI = (92, 74, 60)
LO = (12, 8, 6)
TEXT = (234, 220, 203)  # --text #eadccb
DIM = (156, 138, 122)   # --dim #9c8a7a

# syntax highlight palette from css/style.css (dark side)
ORANGE = (230, 173, 114)  # --kw caramel #e6ad72
PURPLE = (207, 160, 220)  # --dt #cfa0dc
GREEN = (176, 204, 156)   # --st #b0cc9c
YELLOW = (240, 208, 126)  # --fu honey #f0d07e
BLUE = (156, 203, 208)    # --nb #9ccbd0
RED = (238, 144, 112)     # --num cinnamon #ee9070
LINK = (230, 173, 114)    # --link #e6ad72

FONT = ImageFont.load_default_imagefont()


def frame(accent):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=EDGE)
    d.line([1, 1, W - 2, 1], fill=HI)
    d.line([1, 1, 1, H - 2], fill=HI)
    d.line([1, H - 2, W - 2, H - 2], fill=LO)
    d.line([W - 2, 1, W - 2, H - 2], fill=LO)
    # left panel
    d.rectangle([3, 3, 23, H - 4], fill=accent)
    d.line([24, 3, 24, H - 4], fill=LO)
    return img, d


def text(d, top, bottom, accent):
    x0 = 28
    d.text((x0, 4), top, font=FONT, fill=DIM)
    d.text((x0, 16), bottom, font=FONT, fill=accent)


def bitmap(d, rows, x, y, color):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "X":
                d.point((x + i, y + j), fill=color)


LAMBDA = [
    "XX.......",
    ".XX......",
    "..X......",
    "..XX.....",
    "...X.....",
    "..XXX....",
    "..X.X....",
    ".XX.XX...",
    ".X...X...",
    "XX...XX..",
    "X.....XX.",
]

JS = [
    "..XXX..XXXX",
    "...X..X....",
    "...X..X....",
    "...X...XXX.",
    "...X......X",
    "X..X......X",
    ".XX...XXXX.",
]

CC = [
    "..XXX....XXX.",
    ".X......X....",
    "X......X.....",
    "X......X.....",
    "X......X.....",
    ".X......X....",
    "..XXX....XXX.",
]


def hakyll():
    img, d = frame(PURPLE)
    bitmap(d, LAMBDA, 9, 10, BG)
    text(d, "built w/", "HAKYLL", PURPLE)
    return img


def nojs():
    img, d = frame(YELLOW)
    bitmap(d, JS, 8, 12, BG)
    d.line([5, H - 7, 21, 6], fill=RED, width=2)
    text(d, "100%", "NO JS", YELLOW)
    return img


def rss():
    img, d = frame(ORANGE)
    ox, oy = 7, 23  # bottom-left origin of the icon
    d.rectangle([ox, oy - 2, ox + 2, oy], fill=BG)
    for r in (7, 12):
        d.arc([ox - r, oy - r, ox + r, oy + r], 270, 360, fill=BG, width=2)
    text(d, "subscribe", "RSS FEED", ORANGE)
    return img


def ccby():
    img, d = frame(GREEN)
    d.ellipse([4, 6, 23, 25], outline=BG, width=2)
    bitmap(d, CC, 7, 12, BG)
    text(d, "content", "CC-BY 4.0", GREEN)
    return img


def puffer(d, cx, cy, r, spikes):
    """Draw a pufferfish centered at (cx, cy); r grows as it inflates."""
    ry = max(3, int(r * (0.55 + 0.45 * spikes)))
    # tail
    d.polygon([(cx - r - 4, cy - 3), (cx - r - 4, cy + 3), (cx - r + 1, cy)], fill=BG)
    d.ellipse([cx - r, cy - ry, cx + r, cy + ry], fill=BG)
    if spikes:
        for k in range(14):
            a = 2 * math.pi * k / 14
            x = cx + (r + 2) * math.cos(a)
            y = cy + (ry + 2) * math.sin(a)
            d.point((round(x), round(y)), fill=BG)
    # belly highlight, eye, mouth
    d.point((cx + r - 3, cy - ry // 2), fill=TEXT)
    d.point((cx + r, cy + 1), fill=BLUE)


def fugu_frames():
    frames = []
    for r, s in ((4, 0.0), (5, 0.4), (6, 0.8), (7, 1.0)):
        img, d = frame(BLUE)
        puffer(d, 15, 15, r, s)
        text(d, "fugu.cafe", "LINK ME!", LINK)
        frames.append(img)
    return frames


def icon(n):
    """Pixel pufferfish on the site background, drawn natively at n px."""
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=max(2, n // 6), fill=BG)
    k = n / 32
    cx, cy, r = round(17 * k), round(16 * k), round(9 * k)
    # tail
    d.polygon(
        [(cx - r - round(5 * k), cy - round(4 * k)),
         (cx - r - round(5 * k), cy + round(4 * k)),
         (cx - r + 1, cy)],
        fill=BLUE,
    )
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE)
    # spikes
    count = 12 if n >= 32 else 8
    for i in range(count):
        a = 2 * math.pi * (i + 0.5) / count
        for step in (1, 2) if n >= 32 else (1,):
            x = cx + (r + step) * math.cos(a)
            y = cy + (r + step) * math.sin(a)
            d.point((round(x), round(y)), fill=BLUE)
    # eye and mouth
    e = max(1, round(2 * k))
    ex, ey = cx + round(3 * k), cy - round(3 * k)
    d.rectangle([ex, ey, ex + e - 1, ey + e - 1], fill=BG)
    d.point((cx + r - 1, cy + round(2 * k)), fill=BG)
    return img


def icons(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    i16, i32, i48 = icon(16), icon(32), icon(48)
    i32.save(out / "favicon-32.png", optimize=True)
    # ico: save from the largest frame so every native size is kept
    i48.save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
             append_images=[i16, i32])
    # apple touch: opaque, 32px art scaled 5x with nearest neighbour, padded
    touch = Image.new("RGB", (180, 180), BG)
    big = i32.resize((160, 160), Image.NEAREST)
    touch.paste(big, (10, 10), big)
    touch.save(out / "apple-touch-icon.png", optimize=True)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in (("hakyll", hakyll), ("no-js", nojs), ("rss", rss), ("cc-by", ccby)):
        fn().save(out / f"{name}.png", optimize=True)

    frames = fugu_frames()
    # static fallback: fully inflated
    frames[-1].save(out / "fugu-cafe.png", optimize=True)
    seq = frames + frames[-2:0:-1]
    durations = [900] + [120] * (len(frames) - 2) + [1400] + [120] * (len(frames) - 2)
    pal = [f.quantize(colors=32, method=Image.Quantize.MEDIANCUT) for f in seq]
    pal[0].save(
        out / "fugu-cafe.gif",
        save_all=True,
        append_images=pal[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    # usage: badges.py <badges-dir> [icons-dir]
    main(sys.argv[1])
    if len(sys.argv) > 2:
        icons(sys.argv[2])
