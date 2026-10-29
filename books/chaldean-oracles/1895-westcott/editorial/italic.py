# The italic, which neither reading of the scan records: the slant of each
# word's strokes on the page (the measure of
# ../sepher-yetzirah/italic.py: a word's columns of ink are sharpest when
# sheared back by its own slant; ratio = the score at the italic's slant
# over the score upright, above 1 for italic). The text's italic (its *…*)
# is read against it word by word (the text aligned with Tesseract's words,
# ocr/tess/NN.tsv); a word the measure is sure of and the text sets the
# other way is printed, to be read on the page.
#
#   python3 italic.py [oracles-edited.txt]       the places
#   python3 italic.py --page N                    each word on a page, its ratio

import csv
import difflib
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "sepher-yetzirah"))
from italic import score  # noqa: E402

SLANT = 0.22
ITALIC, ROMAN = 1.05, 0.9  # sure above / below (p. 6: roman 0.58–0.81, italic 1.15–1.56)
W = r"[A-Za-zæÆœŒéèëÉË]+|\d+"


def key(w):
    return w.lower().replace("æ", "ae").replace("œ", "oe").replace("é", "e").replace("è", "e").replace("ë", "e")


def page_words(n):
    im = np.array(Image.open(HERE / "pages" / f"p-{n:02d}.png").convert("L")) < 128
    out = []
    for r in csv.DictReader(open(HERE / "ocr/tess" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not r["text"].strip():
            continue
        l, t, w, h = (int(r[k]) for k in ("left", "top", "width", "height"))
        ratio = None
        letters = re.sub(r"[^A-Za-z]", "", r["text"])
        if len(letters) >= 3 and h > 10:
            crop = im[t : t + h, l : l + w]
            s0 = score(crop, 0.0)
            ratio = score(crop, SLANT) / s0 if s0 else None
        for m in re.finditer(W, r["text"]):
            out.append((key(m.group()), ratio, n, r["text"]))
    # a word broken at a line's end ("Hup-", "arche") is one
    joined = []
    for w in out:
        if joined and joined[-1][3].endswith("-") and w[3] != joined[-1][3]:
            a = joined.pop()
            w = (a[0] + w[0], a[1], n, a[3] + w[3])
        joined.append(w)
    return joined


if __name__ == "__main__" and sys.argv[1:2] == ["--page"]:
    for w, ratio, _, t in page_words(int(sys.argv[2])):
        print(f"{ratio if ratio is None else round(ratio, 3)!s:>6}  {t}")
    sys.exit()

path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "oracles-edited.txt"
text = []  # (key, italic?, page, context)
for line in path.read_text().splitlines():
    tag, _, body = line.partition("\t")
    if tag in ("@part", "@note") or body.startswith(("<H>", "{{")):
        continue  # (the notes are checked where they stand: see below)
    body = re.sub(r"<[^>]+>|\[\^\d+\]|\\n", " ", body)
    it = False
    for m in re.finditer(rf"\*|{W}", body):
        if m.group() == "*":
            it = not it
        else:
            text.append((key(m.group()), it, tag[1:], body[max(0, m.start() - 40) : m.end() + 25]))
notes = []
for line in path.read_text().splitlines():
    tag, _, body = line.partition("\t")
    if tag == "@note":
        body = re.sub(r"^\[\^\d+\]: ", "", body)
        it = False
        for m in re.finditer(rf"\*|{W}", body):
            if m.group() == "*":
                it = not it
            else:
                notes.append((key(m.group()), it, "note", body[max(0, m.start() - 40) : m.end() + 25]))

ocr = [w for n in range(3, 55) for w in page_words(n)]
n = 0
for words in (text, notes):
    sm = difflib.SequenceMatcher(None, [w[0] for w in words], [w[0] for w in ocr], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        # (a run the OCR misreads word for word, "Zim." for "Tim.", is
        # paired word by word too)
        if op not in ("equal", "replace") or op == "replace" and i2 - i1 != j2 - j1 or i2 - i1 < 3 and words is notes and op == "equal":
            continue
        for k in range(i2 - i1):
            w, it, page, ctx = words[i1 + k]
            ratio = ocr[j1 + k][1]
            if ratio is None:
                continue
            if (ratio > ITALIC and not it) or (ratio < ROMAN and it):
                n += 1
                print(f"p.{ocr[j1 + k][2]:>3}  {'roman' if not it else 'ITALIC'} in text, {round(ratio, 3)}   {ocr[j1 + k][3]!r}   …{ctx}…")
print(f"{n} places", file=sys.stderr)
