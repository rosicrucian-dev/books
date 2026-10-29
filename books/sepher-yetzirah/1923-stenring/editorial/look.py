# Crops the page renders (pages/p-NN.png, 300 dpi) around words, to read a
# place on the page: each argument "<pdf page>:<A~B~…>" finds the first
# run of Tesseract's words (ocr/tsv/NN.tsv) matching the regexes in turn
# and crops its line and the lines either side; "<pdf page>:@<x0>,<y0>,
# <x1>,<y1>" crops a box (300 dpi pixels). The crops are stacked into one
# image.
#
#   python3 look.py out.png 11:Calomira 13:Twelve~Simple

import csv
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent

out, specs = sys.argv[1], sys.argv[2:]
crops = []
for spec in specs:
    n, pat = spec.split(":", 1)
    n = int(n)
    im = Image.open(HERE / "pages" / f"p-{n:02d}.png").convert("RGB")
    if pat.startswith("@"):
        x0, y0, x1, y1 = map(int, pat[1:].split(","))
        c = im.crop((x0, y0, x1, y1))
        label = spec
    else:
        rows = [r for r in csv.DictReader(open(HERE / "ocr/tsv" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE) if r["level"] == "5" and r["text"].strip()]
        pats = pat.split("~")
        hit = None
        for i in range(len(rows) - len(pats) + 1):
            if all(re.search(q, rows[i + j]["text"]) for j, q in enumerate(pats)):
                hit = rows[i + len(pats) - 1]
                break
        if not hit:
            c = im.resize((im.width // 3, im.height // 3))
            label = f"{spec}: not found, whole page"
        else:
            l, t, w, h = (int(hit[k]) for k in ("left", "top", "width", "height"))
            top = max(0, t - 70)
            c = im.crop((0, top, im.width, min(im.height, t + h + 70)))
            ImageDraw.Draw(c).rectangle((l - 3, t - top - 3, l + w + 3, t - top + h + 3), outline=(220, 0, 0), width=2)
            label = spec
    c = c.resize((c.width * 2 // 3, c.height * 2 // 3))
    lab = Image.new("RGB", (c.width, 20), "white")
    ImageDraw.Draw(lab).text((6, 4), label, fill=(0, 0, 160))
    crops += [lab, c]
W = max(c.width for c in crops)
sheet = Image.new("RGB", (W, sum(c.height for c in crops)), "white")
y = 0
for c in crops:
    sheet.paste(c, (0, y))
    y += c.height
sheet.save(out)
print(out, sheet.size)
