# Crops the 1895 scans (source/unknown-world-1895/<issue>.pdf) around
# words, to read a place on the page: each argument "<letter>:<A~B~…>"
# (letter 1–6, its issue) finds the first run of OCR words matching the
# regexes in turn (<issue>.xml, the OCR's coordinates) and crops its line
# and the lines either side; the crops are stacked into one image.
#
#   python3 look.py out.png 3:The~right 2:every~force

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent / "source" / "unknown-world-1895"
ISSUES = ["v1_n6_jan_15_1895", "v2_n1_feb_15_1895", "v2_n2_mar_15_1895", "v2_n3_apr_15_1895", "v2_n4_may_15_1895", "v2_n5_jun_15_1895"]
WORD = r'<WORD coords="(\d+),(\d+),(\d+),(\d+)[^"]*"[^>]*>([^<]*)</WORD>'

out, specs = sys.argv[1], sys.argv[2:]
crops = []
tmp = Path(tempfile.mkdtemp())
pages = {}
for spec in specs:
    k, pat = spec.split(":", 1)
    issue = ISSUES[int(k) - 1]
    if issue not in pages:
        xml = (HERE / f"{issue}.xml").read_text()
        pages[issue] = re.findall(r'<OBJECT[^>]*width="(\d+)" height="(\d+)">(.*?)</OBJECT>', xml, re.S)
    pats = pat.split("~")
    hit = None
    for n, (w, h, body) in enumerate(pages[issue], 1):
        ws = list(re.finditer(WORD, body))
        for i in range(len(ws) - len(pats) + 1):
            if all(re.search(q, ws[i + j].group(5), re.I) for j, q in enumerate(pats)):
                hit = (n, int(w), int(h), tuple(int(v) for v in ws[i].groups()[:4]))
                break
        if hit:
            break
    if not hit:
        lab = Image.new("RGB", (600, 22), "white")
        ImageDraw.Draw(lab).text((6, 4), f"{spec}: not found", fill=(200, 0, 0))
        crops.append(lab)
        continue
    n, w, h, (l, b, r, t) = hit
    png = tmp / f"{issue}-{n}.png"
    if not png.exists():
        subprocess.run(["pdftoppm", "-r", "150", "-f", str(n), "-l", str(n), "-singlefile", "-png", str(HERE / f"{issue}.pdf"), str(png)[:-4]], check=True)
    im = Image.open(png).convert("RGB")
    sx, sy = im.width / w, im.height / h
    top = max(0, t - 140)
    c = im.crop((0, int(top * sy), im.width, min(im.height, int((b + 140) * sy))))
    ImageDraw.Draw(c).rectangle((int(l * sx) - 3, int((t - top) * sy) - 3, int(r * sx) + 3, int((b - top) * sy) + 3), outline=(220, 0, 0), width=2)
    lab = Image.new("RGB", (c.width, 22), "white")
    ImageDraw.Draw(lab).text((6, 4), f"{spec} (scan p.{n})", fill=(0, 0, 160))
    crops += [lab, c]
W = max(c.width for c in crops)
sheet = Image.new("RGB", (W, sum(c.height for c in crops)), "white")
y = 0
for c in crops:
    sheet.paste(c, (0, y))
    y += c.height
sheet.save(out)
print(out, sheet.size)
