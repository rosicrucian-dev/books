# Builds the site's text of The Cloud upon the Sanctuary, Isabel de
# Steiger's translation, third issue, revised and enlarged, with A. E.
# Waite's introduction (London: William Rider & Son, [1909]), from the
# sacred-texts.com transcription of it:
#
#   extract.py   the transcription's paragraphs, by page (cloud.txt), the
#                print's three misprints (sacred-texts' errata) restored
#   edits.json   every change made to them, each with its reason
#   compare.py   the Letters against the translation's first printing (The
#                Unknown World, 1895: its scans' OCR and adepti.com's
#                transcription), word by word (run on cloud-edited.txt,
#                which this writes)
#   look.py      crops of the 1895 scans, to read a place on the page
#
#   python3 build.py
#
# writes ../cloud-upon-the-sanctuary/
# 01.mdx, 02.mdx …: the Introduction (1), then Letters I–VI (2–7), as
# books.json's "parts" name them. De Steiger's notes are footnotes, numbered
# from 1 on each page. Every edit must match as many times as it says (once,
# unless "count"), or the build stops.

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parent
LABELS = ["Introduction", "Letter I", "Letter II", "Letter III", "Letter IV", "Letter V", "Letter VI and Last"]
edits = json.loads((HERE / "edits.json").read_text())

lines = subprocess.run([sys.executable, "-I", str(HERE / "extract.py")], capture_output=True, text=True, check=True).stdout
(HERE / "cloud.txt").write_text(lines)

failed = []
for e in edits:
    n = lines.count(e["find"])
    if n != e.get("count", 1):
        failed.append(f'{n}x (wants {e.get("count", 1)}): {e["find"][:70]!r}')
        continue
    lines = lines.replace(e["find"], e["replace"])
if failed:
    sys.exit("edits that do not match as they say:\n  " + "\n  ".join(failed))
(HERE / "cloud-edited.txt").write_text(lines)

parts, notes = [], {}
for line in lines.splitlines():
    tag, text = line.split("\t", 1)
    if tag == "@part":
        parts.append([text, []])
    elif tag == "@note":
        m = re.match(r"\[\^(\d+)\]: (.*)", text)
        notes[m.group(1)] = m.group(2)
    else:
        parts[-1][1].append(text)

if [p[0] for p in parts] != LABELS:
    sys.exit(f"parts: {[p[0] for p in parts]}")

SITE.mkdir(parents=True, exist_ok=True)
for old in SITE.glob("[0-9][0-9].mdx"):
    old.unlink()
words = 0
for i, (label, paras) in enumerate(parts, 1):
    text = "\n\n".join(paras) + "\n"
    # This page's notes, numbered from 1.
    order = {old: str(k) for k, old in enumerate(re.findall(r"\[\^(\d+)\]", text), 1)}
    text = re.sub(r"\[\^(\d+)\]", lambda m: f"[^{order[m.group(1)]}]", text)
    for old, new in order.items():
        text += f"\n[^{new}]: {notes.pop(old)}\n"
    if re.search(r"[{}<]", text):
        sys.exit(f"{label}: text has {{ }} or < that MDX would read as code")
    (SITE / f"{i:02d}.mdx").write_text(text)
    words += len(text.split())
if notes:
    sys.exit(f"notes not referenced: {sorted(notes)}")
print(f"{SITE}: {len(parts)} parts, {words} words")
