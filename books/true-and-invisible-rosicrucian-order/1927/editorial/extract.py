# The transcription's paragraphs (source.pdf, a Word file made into a PDF
# in 2003), one per line, each tagged with the page it starts on:
#
#   @<page>\t<text>
#
# Italic and bold are kept as *…* and **…**; a glyph in the Siddur
# (Hebrew) or Symbol font as {heb:…} or {sym:…}. A paragraph ends where
# the next line is set apart (Word's space after a paragraph) or the line
# is short (a line break typed within one); one that runs on over a page
# break is joined. The page numbers at the head of each page are dropped.
#
#   python3 -m venv /tmp/v && /tmp/v/bin/pip install pdfminer.six
#   /tmp/v/bin/python extract.py source.pdf > paragraphs.txt

import sys

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTTextBox, LTTextLine

SHORT = 440  # a line ending left of this (pt) ends its paragraph
GAP = 5  # more space than this above a line starts a paragraph

MARK = {"i": ("*", "*"), "b": ("**", "**"), "heb": ("{heb:", "}"),
        "sym": ("{sym:", "}"), "": ("", "")}


def style(font):
    if "Siddur" in font:
        return "heb"
    if "Symbol" in font:
        return "sym"
    if "Bold" in font:
        return "b"
    if "Italic" in font:
        return "i"
    return ""


def runs_of(line):
    runs = []
    for ch in line:
        t = ch.get_text().replace("\n", "")
        if not t:
            continue
        if isinstance(ch, LTChar) and not t.isspace():
            s = style(ch.fontname)
        else:
            s = runs[-1][0] if runs else ""
        if runs and runs[-1][0] == s:
            runs[-1][1] += t
        else:
            runs.append([s, t])
    return runs


def render(runs):
    out = ""
    for s, t in runs:
        a, b = MARK[s]
        if a and t.strip():
            lead = t[: len(t) - len(t.lstrip())]
            trail = t[len(t.rstrip()):]
            out += lead + a + t.strip() + b + trail
        else:
            out += t
    return " ".join(out.split())


paras = []  # [page, runs, last line's right edge]
for pno, page in enumerate(extract_pages(sys.argv[1], laparams=LAParams()), 1):
    lines = sorted(
        (l for b in page if isinstance(b, LTTextBox) for l in b
         if isinstance(l, LTTextLine) and l.get_text().strip()),
        key=lambda l: -l.y1,
    )
    if pno > 1 and lines and lines[0].get_text().strip().isdigit():
        lines = lines[1:]  # the page number
    prev = None
    for l in lines:
        runs = runs_of(l)
        if prev is None:
            # Top of a page: runs on from the last page's paragraph unless
            # that ended short.
            new = not paras or paras[-1][2] < SHORT or pno == 2
        else:
            new = prev.y0 - l.y1 > GAP or prev.x1 < SHORT
        if new:
            paras.append([pno, runs, l.x1])
        else:
            last = paras[-1][1]
            if not (last and last[-1][1].rstrip().endswith("-")):
                last[-1][1] += " "
            if runs and last and last[-1][0] == runs[0][0]:
                last[-1][1] += runs.pop(0)[1]
            last.extend(runs)
            paras[-1][2] = l.x1
        prev = l

for pno, runs, _ in paras:
    text = render(runs)
    if text:
        print(f"@{pno}\t{text}")
