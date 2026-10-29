# halves.py N OUTDIR: the page render in two halves, for proofreading.
import sys
from pathlib import Path
from PIL import Image
n, out = int(sys.argv[1]), Path(sys.argv[2])
im = Image.open(Path(__file__).parent / "pages" / f"p-{n:02d}.png")
w, h = im.size
im.crop((90, 130, w - 70, h // 2 + 70)).save(out / f"pg{n}a.png")
im.crop((90, h // 2 - 70, w - 70, h - 110)).save(out / f"pg{n}b.png")
