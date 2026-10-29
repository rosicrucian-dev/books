# Crops the scan (source/scan.pdf) around words, to read them on the page:
# each argument "<printed page>:<regex>" finds the first OCR word matching
# the regex on that page or the two after it (source/scan-djvu.xml's
# coordinates; the running head left out) and crops its line and the lines
# either side; the crops are stacked into one image.
#
#   python3 look.py out.png 75:Relative 120:sub

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
xml = (HERE / "source/scan-djvu.xml").read_text()
objs = re.findall(r'<OBJECT[^>]*width="(\d+)" height="(\d+)">(.*?)</OBJECT>', xml, re.S)

out, specs = sys.argv[1], sys.argv[2:]
crops = []
tmp = Path(tempfile.mkdtemp())
for spec in specs:
    p, pat = spec.split(":", 1)
    hit = None
    for n in range(int(p) + 4, int(p) + 7):
        w, h, body = objs[n - 1]
        w, h = int(w), int(h)
        # "A~B": a word matching B just after one matching A.
        pats = pat.split("~")
        ws = list(re.finditer(r'<WORD coords="(\d+),(\d+),(\d+),(\d+)[^"]*"[^>]*>([^<]*)</WORD>', body))
        for k in range(len(ws) - len(pats) + 1):
            m = ws[k + len(pats) - 1]
            if int(m.group(4)) > 0.12 * h and all(re.search(q, ws[k + i].group(5)) for i, q in enumerate(pats)):
                hit = tuple(int(v) for v in m.groups()[:4])
                break
        if hit:
            break
    if not hit:
        n = int(p) + 4
        w, h, body = objs[n - 1]
        w, h = int(w), int(h)
    png = tmp / f"p{n}.png"
    if not png.exists():
        subprocess.run(["pdftoppm", "-r", "150", "-f", str(n), "-l", str(n), "-singlefile", "-png", str(HERE / "source/scan.pdf"), str(png)[:-4]], check=True)
    im = Image.open(png).convert("RGB")
    sx, sy = im.width / w, im.height / h
    if hit is None:
        c = im.resize((im.width // 2, im.height // 2))
        label = f"{spec}: not found, whole page"
    else:
        l, b, r, t = hit
        c = im.crop((0, max(0, int((t - 110) * sy)), im.width, min(im.height, int((b + 110) * sy))))
        ImageDraw.Draw(c).rectangle((int(l * sx) - 3, int((t - (t - 110 if t > 110 else 0)) * sy) - 3, int(r * sx) + 3, int((b - (t - 110 if t > 110 else 0)) * sy) + 3), outline=(220, 0, 0), width=2)
        label = spec
    lab = Image.new("RGB", (c.width, 22), "white")
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
