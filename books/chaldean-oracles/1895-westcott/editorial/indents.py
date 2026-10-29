# Whether each page's first line of text is set in from the margin (a
# paragraph begins there) or not (the last page's runs on), from
# Tesseract's word boxes (ocr/tess/NN.tsv): the first line under the page
# number against the page's margin, where most lines begin. The scan's PDF
# page is the printed page from 3 on. Writes source/indents.json, which
# extract.py reads; a page whose first line is a heading or centred is
# "set in" too, which is what extract.py needs (no run-on).
#
#   python3 indents.py

import csv
import re
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
out = {}
for n in range(4, 55):
    lines = {}
    for r in csv.DictReader(open(HERE / "ocr/tess" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not r["text"].strip():
            continue
        k = (r["block_num"], r["par_num"], r["line_num"])
        top, left = int(r["top"]), int(r["left"])
        t, l, words = lines.get(k, (top, left, []))
        lines[k] = (min(t, top), min(l, left), words + [r["text"]])
    ls = sorted(lines.values())
    # the running number: a line of digits alone at the head
    # (Tesseract reads some as "I5", "II")
    while ls and re.fullmatch(r"[\dIlO]{1,2}", "".join(ls[0][2])):
        ls.pop(0)
    # the leftmost edge three lines or more share (a page of short oracles
    # has more lines set in than not)
    c = Counter(round(l / 10) * 10 for _, l, _ in ls)
    margin = min(x for x, k in c.items() if k >= 3)
    first = ls[0]
    out[str(n)] = first[1] > margin + 30
    print(n, margin, first[1], out[str(n)], " ".join(first[2])[:50])
(HERE / "source/indents.json").write_text(json.dumps(out, indent=0) + "\n")
