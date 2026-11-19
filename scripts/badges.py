"""Generate 88x31 badges for fugu.cafe using the site's own palette."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 88, 31
BG = (17, 17, 17)
EDGE = (42, 42, 42)
HI = (70, 70, 70)
LO = (5, 5, 5)
TEXT = (216, 216, 216)
DIM = (143, 143, 143)

# syntax highlight palette from css/style.css
ORANGE = (255, 184, 108)
PURPLE = (189, 147, 249)
GREEN = (165, 214, 167)
YELLOW = (255, 213, 79)
BLUE = (129, 212, 250)
RED = (247, 140, 108)
LINK = (138, 180, 248)

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
    main(sys.argv[1])
