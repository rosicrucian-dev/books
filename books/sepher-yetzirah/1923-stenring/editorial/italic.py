# Which words the page sets in italic, which neither reading records: the
# slant of their strokes. Each word Tesseract finds (ocr/tsv/NN.tsv) is cut
# from the page render (pages/p-NN.png, 300 dpi) and sheared back by a
# range of slants; the slant at which its strokes stand most nearly upright
# (the columns of ink sharpest: the sum of their squares greatest) is its
# lean. Roman type stands at 0; this italic leans about 1 in 5.
#
#   python3 italic.py <pdf page> [--show]   prints each word with its lean

import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SLANTS = np.linspace(-0.1, 0.4, 26)


def score(a, s):
    """How sharply the word's strokes stand upright once sheared back by s:
    the sum of the squares of its columns of ink."""
    h, w = a.shape
    ys = np.arange(h)[::-1]
    shift = np.round(ys * s).astype(int)
    cols = np.zeros(w + int(h * 0.5) + 2)
    for y in range(h):
        row = np.nonzero(a[y])[0]
        if len(row):
            np.add.at(cols, row - shift[y] + int(h * 0.15) + 1, 1)
    return (cols ** 2).sum()


def lean(a):
    """The shear (x shift per unit of height, rightward up) that makes the
    word's strokes most upright."""
    h, w = a.shape
    ys = np.arange(h)[::-1]  # height above the foot
    best, at = -1, 0
    for s in SLANTS:
        shift = np.round(ys * s).astype(int)
        cols = np.zeros(w + int(h * 0.5) + 2)
        for y in range(h):
            row = np.nonzero(a[y])[0]
            if len(row):
                np.add.at(cols, row - shift[y] + int(h * 0.15) + 1, 1)
        score = (cols ** 2).sum()
        if score > best:
            best, at = score, s
    return at


def words(n):
    im = np.array(Image.open(HERE / "pages" / f"p-{n:02d}.png").convert("L")) < 128
    out = []
    for r in csv.DictReader(open(HERE / "ocr/tsv" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not r["text"].strip():
            continue
        l, t, w, h = (int(r[k]) for k in ("left", "top", "width", "height"))
        crop = im[t : t + h, l : l + w]
        letters = sum(c.isalpha() for c in r["text"])
        out.append(dict(text=r["text"], box=(l, t, w, h), line=(r["block_num"], r["par_num"], r["line_num"]), lean=lean(crop) if letters >= 2 and h > 10 else None))
    return out


if __name__ == "__main__":
    n = int(sys.argv[1])
    for w in words(n):
        print(f"{w['lean'] if w['lean'] is not None else '-':>6}  {w['text']}")
