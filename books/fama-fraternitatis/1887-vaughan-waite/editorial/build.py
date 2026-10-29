# Builds the site's texts of the Fama Fraternitatis and the Confessio
# Fraternitatis in Waite's edition (The Real History of the Rosicrucians,
# 1887; Vaughan's translation of 1652, the Confessio revised by Waite)
# from the sacred-texts.com transcription:
#
#   extract.py   the transcription's paragraphs (fama.txt, confessio.txt)
#   edits.json   every change made to them, each with its reason:
#                "typing" (the transcription's slips, read against the
#                1887 print, source/scan.pdf), "structure" (an inscription
#                or a list set apart as printed)
#   compare.py   the text against the print's OCR, word by word
#
#   python3 build.py
#
# writes ../../{fama,confessio}-fraternitatis/
# text.mdx. Waite's footnotes are kept, numbered from 1 in each. Every
# edit must match exactly once, or the build stops.

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parents[2]
edits = json.loads((HERE / "edits.json").read_text())

for which in ("fama", "confessio"):
    lines = subprocess.run([sys.executable, "-I", str(HERE / "extract.py"), which], capture_output=True, text=True, check=True).stdout
    (HERE / f"{which}.txt").write_text(lines)
    paras, notes = [], []
    for line in lines.splitlines():
        tag, text = line.split("\t", 1)
        (notes if tag == "@note" else paras).append(text)
    text = "\n\n".join(paras) + "\n"

    failed = []
    for e in (e for e in edits if e["text"] == which):
        n = text.count(e["find"])
        if n != 1:
            failed.append(f'{n}x: {e["find"][:70]!r}')
            continue
        text = text.replace(e["find"], e["replace"])
    if failed:
        sys.exit(f"{which}: edits that do not match exactly once:\n  " + "\n  ".join(failed))

    # Waite's footnotes, numbered from 1.
    order = {old: str(i) for i, old in enumerate(re.findall(r"\[\^(\d+)\]", text), 1)}
    text = re.sub(r"\[\^(\d+)\]", lambda m: f"[^{order[m.group(1)]}]", text)
    for note in notes:
        old = re.match(r"\[\^(\d+)\]", note).group(1)
        text += "\n" + note.replace(f"[^{old}]", f"[^{order[old]}]", 1) + "\n"

    if re.search(r"[{}<]", text):
        sys.exit(f"{which}: text has {{ }} or < that MDX would read as code")

    out = SITE / f"{which}-fraternitatis" / "1887-vaughan-waite" / "text.mdx"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"{out}: {len(text.split())} words")
