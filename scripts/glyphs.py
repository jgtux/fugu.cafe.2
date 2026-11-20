"""Check that every character in the articles exists in the self-hosted fonts.

Prose is checked against New Computer Modern, code (fenced and inline) against Fira Code.
Math ($...$ and $$...$$) is skipped: it is rendered by the math font.
Exits 1 and lists the missing characters, so it can gate a build.
"""
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SERIF = ["new-cm-400-normal", "new-cm-400-italic",
         "new-cm-700-normal", "new-cm-700-italic"]
MONO = ["fira-code"]

FENCE = re.compile(r"^```.*?^```", re.S | re.M)
INLINE_CODE = re.compile(r"`[^`\n]+`")
MATH = re.compile(r"\$\$.+?\$\$|(?<![\\\w])\$[^\s$][^$\n]*?\$", re.S)
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


def cmap(names):
    """Characters present in all the given font files."""
    sets = [set(TTFont(ROOT / "fonts" / f"{n}.woff2").getBestCmap()) for n in names]
    return set.intersection(*sets)


def split(text):
    """Return (prose, code) text of one article."""
    text = FRONT_MATTER.sub("", text)
    code = FENCE.findall(text)
    text = FENCE.sub("", text)
    code += INLINE_CODE.findall(text)
    text = INLINE_CODE.sub("", text)
    text = MATH.sub("", text)
    return text, "".join(code)


def missing(text, chars):
    return sorted({c for c in text if ord(c) > 127 and ord(c) not in chars})


def main():
    serif, mono = cmap(SERIF), cmap(MONO)
    bad = 0
    for path in sorted((ROOT / "articles").glob("*.md")):
        prose, code = split(path.read_text(encoding="utf-8"))
        for kind, chars in (("prose", missing(prose, serif)), ("code", missing(code, mono))):
            if chars:
                bad += 1
                shown = " ".join(f"{c} U+{ord(c):04X}" for c in chars)
                print(f"{path.name}: {kind} missing {shown}")
    if bad:
        sys.exit(1)
    print("all article characters covered")


if __name__ == "__main__":
    main()
