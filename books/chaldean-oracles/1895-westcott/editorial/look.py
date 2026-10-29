# Crops the scan's pages (pages/p-NN.png, 300 dpi; the PDF page is the
# printed page from 3 on) around a place, to read it on the page: each
# argument "<printed page>:<regex>" finds the first line of Tesseract's
# (ocr/tess/NN.tsv, its words joined by spaces) the regex matches, case
# ignored, on that page, and crops it with the line before and after; the
# crops are stacked into one image, each labelled.
#
#   python3 look.py out.png 12:Law.under 32:Swift

import csv
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent


def lines(n):
    ls = {}
    for r in csv.DictReader(open(HERE / "ocr/tess" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not r["text"].strip():
            continue
        k = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
        t, b = int(r["top"]), int(r["top"]) + int(r["height"])
        top, bot, words = ls.get(k, (t, b, []))
        ls[k] = (min(top, t), max(bot, b), words + [r["text"]])
    return sorted(ls.values())


out, specs = sys.argv[1], sys.argv[2:]
crops = []
for spec in specs:
    p, pat = spec.split(":", 1)
    # "+N" after the page: N more lines after the one found
    p, _, more = p.partition("+")
    more = int(more or 0)
    at = None
    for n in [k for k in (int(p), int(p) + 1) if k <= 54]:  # (or the next page)
        ls = lines(n)
        at = next((i for i, l in enumerate(ls) if re.search(pat, " ".join(l[2]), re.I)), None)
        if at is not None:
            break
    im = Image.open(HERE / "pages" / f"p-{n:02d}.png").convert("L")
    if at is None:
        label, box = spec + "  (NOT FOUND)", (0, 0, im.width, 60)
    else:
        a, b = ls[max(0, at - 1)], ls[min(len(ls) - 1, at + 1 + more)]
        label, box = spec, (100, a[0] - 10, im.width - 60, b[1] + 10)
    c = im.crop(box)
    c = c.resize((c.width * 2 // 3, c.height * 2 // 3))
    lab = Image.new("L", (c.width, c.height + 26), 255)
    lab.paste(c, (0, 26))
    ImageDraw.Draw(lab).text((6, 6), label, fill=0)
    crops.append(lab)
W = max(c.width for c in crops)
sheet = Image.new("L", (W, sum(c.height for c in crops)), 255)
y = 0
for c in crops:
    sheet.paste(c, (0, y))
    y += c.height
sheet.save(out)
