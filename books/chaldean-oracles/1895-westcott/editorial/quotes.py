# The quotation marks, which punct.py reads poorly (the scan's text layer
# drops most; Tesseract reads a mark as “ ” " ‘ ’ or ', as it likes): the
# text against Tesseract alone, word by word, a mark any quotation mark not
# between letters; every pair of words the two share where one has a mark
# between them and the other not is printed, to be read on the scan.
#
#   python3 quotes.py [oracles-edited.txt]

import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compare as C  # noqa: E402

Q = re.compile(r"[“”\"‘’'¢]")
W = r"[A-Za-zæÆœŒéèëÉË]+|\d+"


def stream(s, pages=None):
    """(word key, quotation marks after it, page) for each word."""
    s = re.sub(r"(?<=[A-Za-z])[’'](?=[A-Za-z])", "", s)  # apostrophes
    out = []
    for m in re.finditer(rf"({W})((?:(?!{W}).)*)", s, re.S):
        out.append([C.key(m.group(1)), len(Q.findall(m.group(2))), None])
    return out


T = []
for page, b in C.blocks:
    s = stream(re.sub(r"\[\^\d+\]|\*", "", b))
    for x in s:
        x[2] = page
    # a block's opening mark is the last word's of the block before
    lead = len(Q.findall(re.match(rf"((?:(?!{W}).)*)", re.sub(r"<[^>]+>|\*", "", b), re.S).group(1)))
    if T and lead:
        T[-1][1] += lead
    T += s
O = stream(C.tess)
sm = difflib.SequenceMatcher(None, [w for w, _, _ in T], [w for w, _, _ in O], autojunk=False)
n = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != "equal":
        continue
    for k in range(i2 - i1):
        a, b = T[i1 + k], O[j1 + k]
        if (a[1] > 0) != (b[1] > 0):
            i = i1 + k
            n += 1
            print(f"p.{a[2]:>3}  text[{a[1]}]  ocr[{b[1]}]   …{' '.join(x[0] for x in T[max(0, i - 4) : i + 1])} _ {' '.join(x[0] for x in T[i + 1 : i + 4])}…")
print(f"{n} places", file=sys.stderr)
