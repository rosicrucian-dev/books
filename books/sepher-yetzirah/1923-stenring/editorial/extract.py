# The Book of Formation (Sepher Yetzirah), Knut Stenring's translation, with
# A. E. Waite's introduction (London: William Rider & Son, 1923), from the
# Google Books scan of Cornell's copy (source/scan.pdf): the two readings
# of it merged, page by page (ocr/merged/NN.txt, merge.py: italic marked,
# a line set in from the margin marked "¶"), as paragraphs, one per line,
# each tagged with its printed page:
#
#   @<page>\t<text>
#
# and "@part\t<label>" where a part begins. A paragraph begins at a line
# set in from the margin; a page's running head and number are left out; a
# word broken at a line's end is joined (its hyphen kept where the book uses
# the hyphenated form elsewhere, mid-line); italic runs broken only by
# punctuation or a line's end are one. The places the readings differ
# (review.txt), the Hebrew, bold, tables and figures are settled in
# edits.json and figures.json, read on the page.
#
#   python3 extract.py > formation.txt

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
G = HERE / "ocr" / "merged"

# The parts: (label, first PDF page, last PDF page). Plates, the folding
# table and blank pages between them are figures, not text.
PARTS = [
    ("Introduction", 10, 23),
    ("Translator's Note", 24, 26),
    ("Chapter I", 28, 30),
    ("Chapter II", 31, 32),
    ("Chapter III", 34, 35),
    ("Chapter IV", 36, 37),
    ("Chapter V", 38, 39),
    ("Chapter VI", 40, 41),
    ("Notes", 45, 66),
    ("The 32 Paths of Wisdom", 67, 75),
    ("Works Used", 76, 76),
]
# Not text: the plate (20, 21) and blanks (25, 27, 33); the folding wheel
# (32, "to face p. 24"), a figure; Tables II–V (42–44), set from the page
# by hand (tables.md).
SKIP = {20, 21, 25, 27, 32, 33, 42, 43, 44}


def PRINTED(n):
    """A PDF page's printed number: the plate (two leaves after page 14) and
    the table in Chapter II (a leaf and its blank back after page 24) are
    not numbered."""
    return n - 5 if n <= 19 else n - 7 if n <= 31 else n - 9


HEAD = re.compile(r"^\s*(\d+\s+)?(The Book of Formation|Introduction|Notes on [Tt]he Book of Formation|The 32 Paths of Wisdom)(\s+\d+)?\s*$")


def page_lines(n):
    lines = (G / f"{n:02d}.txt").read_text().splitlines()
    lines = [l.rstrip() for l in lines]
    plain = lambda l: l[2:] if l.startswith("¶ ") else l
    # The running head (first non-blank line) and the page number (a line
    # of digits alone, at the foot).
    body = [l for l in lines]
    while body and not body[0].strip():
        body.pop(0)
    printed = None
    if body and HEAD.match(plain(body[0])):
        m = re.search(r"\d+", body[0].replace("32 Paths", ""))
        printed = int(m.group()) if m else None
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if body and re.fullmatch(r"\s*\d+\s*", plain(body[-1])):
        printed = int(plain(body[-1]))
        body.pop()
    # A part's own heads ("THE BOOK OF FORMATION", "CHAPTER I"), the
    # parts' names.
    body = [l for l in body if not re.fullmatch(r"(THE BOOK OF FORMATION|CHAPTER [IVX]+|INTRODUCTION|TRANSLATOR.S NOTE|NOTES ON THE BOOK OF FORMATION|THE 32 PATHS OF WISDOM)\.?", plain(l).strip())]
    return printed, body


texts = []  # whole text, to know which hyphenated forms the book uses
pages = {}
for label, a, b in PARTS:
    for n in range(a, b + 1):
        if n in SKIP:
            continue
        printed, body = page_lines(n)
        pages[n] = (printed, body)
        texts.append("\n".join(body))
alltext = "\n".join(texts)
HYPHENATED = set(m.group().lower() for m in re.finditer(r"\b\w+-\w+\b", re.sub(r"-\n\s*", "", alltext)))
INLINE = set(m.group().lower() for m in re.finditer(r"(?<!\n)\b\w+-\w+\b", alltext))


def join(prev, nxt):
    """A line's end and the next line's start: a word broken by a hyphen is
    whole, unless the book uses its hyphenated form mid-line."""
    m = re.search(r"(\w+)-$", prev)
    if m:
        w = re.match(r"\s*(\w+)", nxt)
        if w and f"{m.group(1)}-{w.group(1)}".lower() in INLINE:
            return prev + nxt.lstrip()
        if w:
            return prev[:-1] + nxt.lstrip()
    return prev + " " + nxt.lstrip()


out = []
expected = None
for label, a, b in PARTS:
    out.append(["part", label])
    para = None
    for n in range(a, b + 1):
        if n not in pages:
            continue
        _, body = pages[n]
        printed = PRINTED(n)
        after_break = True
        for l in body:
            if not l.strip():
                after_break = True
                continue
            new = l.startswith("¶ ")
            l = l[2:] if new else l
            # A numbered verse after a break begins a paragraph, though a
            # stray mark before it hides its indent ("“6. Ten …").
            m = re.match(r"^[\"“‘'*]+\s*(?=(?:[IVX]+\. )?\d+\. )", l)
            if m:
                l = l[m.end():]
            if after_break and re.match(r"(?:[IVX]+\. )?\d+\. ", l) and para is not None and not (first_of_page := False):
                new = True
            after_break = False
            if para is None or new:
                if para:
                    out.append(para)
                para = [printed, l.strip()]
            else:
                para[1] = join(para[1], l.strip())
        # A paragraph runs on over the page unless it ended there.
    if para:
        out.append(para)

def tidy(t):
    t = re.sub(r" {2,}", " ", t)
    # The print's space before ; : ! ? and inside quotation marks is its
    # setting, not the text's.
    t = re.sub(r"\s+([;:!?])", r"\1", t)
    t = re.sub(r"\s+(\*?[;:!?])", r"\1", t)
    t = re.sub(r"([“‘])\s+", r"\1", t)
    t = re.sub(r"\s+([”’])", r"\1", t)
    # An opening “ is closed by ”: Tesseract reads some closing ” as ’ (not
    # an apostrophe: not between letters).
    out, open_ = [], False
    for i, c in enumerate(t):
        if c == "“":
            open_ = True
        elif c == "”":
            open_ = False
        elif c == "’" and open_ and not (i + 1 < len(t) and t[i + 1].isalpha() and i > 0 and t[i - 1].isalpha()):
            c, open_ = "”", False
        out.append(c)
    t = "".join(out)
    # Italic runs broken only by punctuation or a space are one.
    t = re.sub(r"\*([,;:.!?’”)]*)(\s+)\*", r"\1\2", t)
    # A short lowercase word alone in italic among roman ones ("*of*",
    # "*ye*", "*eye*") is the slant measure's error, read on the page each
    # time: roman. Stenring's own italic "*or*" (between alternative
    # forms) and capitalised letter names ("*He*", "*Pe*") stand.
    t = re.sub(r"(?<![*\w])\*(?!or\*)([a-z]{1,3})\*(?![*\w])", r"\1", t)
    # A verse's first word, set in capitals ("1. IN thirty-two"): a word.
    t = re.sub(r"^((?:[IVX]+\. )?\d+\. )?([A-Z]{2,})(?=[ -]+[a-z(])", lambda m: (m.group(1) or "") + m.group(2).capitalize(), t)
    return t


for p in out:
    if p[0] == "part":
        print(f"@part\t{p[1]}")
    else:
        print(f"@{p[0]}\t{tidy(p[1])}")
