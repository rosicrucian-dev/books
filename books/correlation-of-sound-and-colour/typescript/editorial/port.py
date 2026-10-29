#!/usr/bin/env python3
"""How this text came into the repository (October 2026): from the
agelesswisdom site's own tree, where it had been transcribed and
corrected, into the format here. Kept as provenance; it was run once.

    python3 port.py /path/to/agelesswisdom

content/lessons/en/correlation-of-sound-and-colour/NN-<id>.mdx -> NN.mdx, the headings set one
level down (the site's `# Title` is the format's `## Title`, the text's own
top heading); public/images/lessons/correlation-of-sound-and-colour/* -> images/, the figures
referenced from there (`images/<name>`). Nothing in the words is changed.
"""

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDITION = HERE.parent
SRC = Path(sys.argv[1]).resolve()
SECTION = "correlation-of-sound-and-colour"

files = sorted((SRC / "content/lessons/en" / SECTION).glob("*.mdx"))
for i, f in enumerate(files, 1):
    if not f.name.startswith(f"{i:02d}-"):
        raise SystemExit(f"{f.name} is not number {i}")
    text = f.read_text()
    text = re.sub(rf"\]\(/images/lessons/{SECTION}/([^)\s]+)\)", r"](images/\1)", text)
    text = re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", text, flags=re.M)
    (EDITION / f"{i:02d}.mdx").write_text(text)
images = SRC / "public/images/lessons" / SECTION
if images.exists():
    dest = EDITION / "images"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(images, dest)
print(f"{len(files)} files into {EDITION}")
