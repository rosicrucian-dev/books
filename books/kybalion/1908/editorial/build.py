# Builds the site's text of The Kybalion (Chicago: The Yogi Publication
# Society, 1908), the first printing, from the Wikisource transcription of
# it:
#
#   extract.py   the transcription's paragraphs, by page (kybalion.txt)
#   edits.json   every change made to them, each with its reason ("typing":
#                the transcription's slips, read on the 1908 scan,
#                source/scan.pdf); "count" where one change is made in
#                several places
#   compare.py   the text against the scan's OCR and Gutenberg's text, word
#                by word (run on kybalion-edited.txt, which this writes)
#   look.py      crops of the scan, to read a place on the page
#
#   python3 build.py
#
# writes ../kybalion/01.mdx, 02.mdx …: the
# Introduction (1), then Chapters I–XV (2–16), as books.json's "parts"
# name them. Every edit must match as many times as it says (once, unless
# "count"), or the build stops.

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parent
edits = json.loads((HERE / "edits.json").read_text())

lines = subprocess.run([sys.executable, "-I", str(HERE / "extract.py")], capture_output=True, text=True, check=True).stdout
(HERE / "kybalion.txt").write_text(lines)

failed = []
for e in edits:
    n = lines.count(e["find"])
    if n != e.get("count", 1):
        failed.append(f'{n}x (wants {e.get("count", 1)}): {e["find"][:70]!r}')
        continue
    lines = lines.replace(e["find"], e["replace"])
if failed:
    sys.exit("edits that do not match as they say:\n  " + "\n  ".join(failed))
(HERE / "kybalion-edited.txt").write_text(lines)

parts = []  # [label, paragraphs]
for line in lines.splitlines():
    tag, text = line.split("\t", 1)
    if tag == "@part":
        parts.append([text, []])
        continue
    text = text.replace("\\n", "\n")
    # A heading's closing full stop is the print's style, not the heading's.
    text = re.sub(r"^(#{2,3} .*?)\.$", r"\1", text)
    if text == "Finis":
        text = "<Center>Finis</Center>"
    parts[-1][1].append(text)

# The dedication (the print's page after the title's back), centred, its
# lines as printed, at the head of the first part; a rule after it.
ded = re.sub(r"<noinclude>.*?</noinclude>|\{\{dhr\}\}", "", (HERE / "source/wikisource/007.wiki").read_text(), flags=re.S)
while (d := re.sub(r"\{\{[a-z-]+\|([^{}]*)\}\}", r"\1", ded)) != ded:
    ded = d
ded = [" ".join(l.split()) for l in re.split(r"\n\s*\n|<br />", ded) if l.strip()]
parts[0][1][:0] = ["<Center>" + " <br />\n".join(ded) + "</Center>", "---"]

labels = ["Introduction"] + [f"Chapter {r}" for r in "I II III IV V VI VII VIII IX X XI XII XIII XIV XV".split()]
if [p[0] for p in parts] != labels:
    sys.exit(f"parts: {[p[0] for p in parts]}")

SITE.mkdir(parents=True, exist_ok=True)
for old in SITE.glob("[0-9][0-9].mdx"):
    old.unlink()
words = 0
for i, (label, paras) in enumerate(parts, 1):
    text = "\n\n".join(paras) + "\n"
    rest = re.sub(r"<br />|</?Center>", "", text)
    if re.search(r"[{}<]", rest):
        sys.exit(f"{label}: text has {{ }} or < that MDX would read as code")
    (SITE / f"{i:02d}.mdx").write_text(text)
    words += len(text.split())
print(f"{SITE}: {len(parts)} parts, {words} words")
