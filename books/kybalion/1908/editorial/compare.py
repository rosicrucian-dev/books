# Reads the text (kybalion.txt, from Wikisource) against two others, word
# by word: the OCR of the 1908 scan (source/scan-ocr.txt, archive.org
# kybalionstudyofh00thre: the same printing, its errors the machine's) and
# Project Gutenberg's (source/gutenberg.txt, #14209: typed from a later
# printing). A word of the text that neither agrees with is printed, with
# its page and context, to be read on the scan and decided in edits.json;
# so is a run of words both have and the text lacks.
#
#   python3 compare.py [kybalion.txt]

import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "kybalion.txt"

# (The text with edits.json applied: build.py writes kybalion-edited.txt.)

def toks(s):
    return re.findall(r"[A-Za-zæÆ]+|\d+", s)


def key(w):
    return w.lower().replace("æ", "ae")


text, pages = [], []
for line in path.read_text().splitlines():
    tag, _, body = line.partition("\t")
    if tag == "@part" or not body:
        continue
    for w in toks(re.sub(r"<br />|\\n", " ", body)):
        text.append(w)
        pages.append(tag[1:])

ocr = (HERE / "source/scan-ocr.txt").read_text()
ocr = ocr[ocr.index("INTRODUCTION") :]
ocr = re.sub(r"-\s*\n\s*", "", ocr)  # words broken at a line's end
HEADS = re.compile(r"\b(CHAPTER [IVXL]+\.?|INTRODUCTION\.?)")
gut = (HERE / "source/gutenberg.txt").read_text()
gut = gut[gut.index("\nINTRODUCTION") : gut.index("*** END OF THE PROJECT")]
ocr, gut = HEADS.sub(" ", ocr), HEADS.sub(" ", gut)


def differing(other):
    """The indexes of the text's words the other text does not have in
    step, and runs the other has that the text lacks (at an index)."""
    B = toks(other)
    sm = difflib.SequenceMatcher(None, [key(w) for w in text], [key(w) for w in B], autojunk=False)
    bad, extra = set(), {}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("replace", "delete"):
            bad.update(range(i1, i2))
        if op in ("replace", "insert"):
            extra[i1] = " ".join(B[j1:j2])
    return bad, extra


bad_ocr, extra_ocr = differing(ocr)
bad_gut, extra_gut = differing(gut)

n = 0
both = sorted(bad_ocr & bad_gut)
k = 0
while k < len(both):
    i = j = both[k]
    while k + 1 < len(both) and both[k + 1] == j + 1:
        k += 1
        j = both[k]
    k += 1
    n += 1
    print(f"p.{pages[i]:>3}  text[{' '.join(text[i:j + 1])}]  ocr[{extra_ocr.get(i, '')[:40]}]  gut[{extra_gut.get(i, '')[:40]}]   …{' '.join(text[max(0, i - 5):i])} _ {' '.join(text[j + 1:j + 4])}…")
# Words both others have where the text has none.
for i in sorted(set(extra_ocr) & set(extra_gut)):
    if i in bad_ocr or i in bad_gut:
        continue
    a, b = extra_ocr[i].lower().split(), extra_gut[i].lower().split()
    if set(a) & set(b):
        n += 1
        print(f"p.{pages[min(i, len(pages) - 1)]:>3}  text[]  ocr[{extra_ocr[i][:40]}]  gut[{extra_gut[i][:40]}]   …{' '.join(text[max(0, i - 5):i])} _ {' '.join(text[i:i + 3])}…")
print(f"{n} places; {len(text)} words in the text", file=sys.stderr)
