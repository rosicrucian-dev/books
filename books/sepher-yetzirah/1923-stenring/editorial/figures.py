# The book's figures, cut from the scan's own 600 dpi page images (boxes in
# the 300 dpi renders' pixels, pages/, doubled), for the site:
#
#   wheel     the 231 gates, the folding leaf "to face p. 24" (PDF 32),
#             without its running head; the leaf's grey paper set white
#   mothers   Table III's corner symbol, a triangle with a cross (PDF 42)
#   doubles   Table IV's, a hexagram with a dot (PDF 43)
#
# The tables are printed sideways; their symbols are turned upright with
# them. Not used: PDF 20, an engraving of a Maryland marmot and an American
# porcupine bound or scanned into Cornell's copy from another book (the
# text runs on from p. 14 to p. 15 with no plate), and PDF 21, its blank
# back.
#
#   ../../flo/.venv/bin/python figures.py

from pathlib import Path

import fitz
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent / "images"
FIGURES = {
    # name: (PDF page, (x0, y0, x1, y1) at 300 dpi, turn clockwise)
    "wheel": (32, (480, 425, 3130, 3100), False),
    "mothers": (42, (888, 1810, 1002, 1935), True),
    "doubles": (43, (458, 2248, 597, 2376), True),
}

doc = fitz.open(HERE / "source/scan.pdf")
OUT.mkdir(parents=True, exist_ok=True)
for name, (n, box, turn) in FIGURES.items():
    page = doc[n - 1]
    xref = max(page.get_images(), key=lambda i: i[2] * i[3])[0]
    pix = fitz.Pixmap(doc, xref)
    im = Image.frombytes("RGB" if pix.n >= 3 else "L", (pix.width, pix.height), pix.samples).convert("L")
    # The render's pixels to the image's (the render is the page at 300 dpi).
    rw = Image.open(HERE / "pages" / f"p-{n:02d}.png").width
    k = im.width / rw
    im = im.crop(tuple(round(v * k) for v in box))
    a = np.asarray(im).astype(float)
    if name == "wheel":
        # The leaf's paper, shaded towards a corner: divided out, the paper
        # read from the page itself (its lightest pixels nearby, smoothed).
        from PIL import ImageFilter
        small = im.resize((im.width // 16, im.height // 16)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
        paper = np.asarray(small.resize(im.size, Image.BILINEAR)).astype(float)
        a = np.clip(a / np.maximum(paper, 1) * 200, 0, 255)
    # Paper white, ink black (the wheel's leaf is grey).
    lo, hi = np.percentile(a, 2), np.percentile(a, 60)
    a = np.clip((a - lo) * 255 / max(hi - lo - 10, 1), 0, 255).astype("uint8")
    im = Image.fromarray(a)
    if turn:
        im = im.rotate(-90, expand=True)
    im.save(OUT / f"{name}.png", optimize=True)
    print(name, im.size)
