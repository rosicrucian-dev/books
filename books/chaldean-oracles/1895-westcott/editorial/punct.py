# The punctuation: compare.py reads only the words. Here the text and the
# two readings of the scan are cut into words and marks (, ; : . ! ? ( )
# and dashes; a hyphen at a line's end is the line's, not the text's), and
# the marks between each pair of words the three share are compared: where
# both readings agree on them and the text does not, the place is printed,
# to be read on the scan (look.py) and decided in edits.json.
#
#   python3 punct.py [oracles-edited.txt]

import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compare as C  # noqa: E402  (its readings; it prints its own list too)

MARK = re.compile(r"[,;:.!?()\"]|—|-")  # (double quotation marks as \", which way they turn aside)


def stream(s):
    """(word key, the marks after it) for each word."""
    s = re.sub(r"[“”„″]|‘‘|’’|''", '"', s)
    out = []
    for m in re.finditer(r"([A-Za-zæÆœŒéèëÉË]+|\d+)([^A-Za-zæÆœŒéèëÉË\d]*)", s):
        marks = "".join(MARK.findall(m.group(2)))
        out.append((C.key(m.group(1)), marks.replace("-", "—") if "—" in marks or "--" in m.group(2) else marks))
    return out


def text_stream():
    s = []
    for page, b in C.blocks:
        b = re.sub(r"\[\^\d+\]|\*", "", b)
        s += [(w, m, page) for w, m in stream(b)]
    return s


def ocr_stream(t):
    return stream(re.sub(r"\*", "", t))


T = text_stream()
A, B = ocr_stream(C.tess), ocr_stream(C.layer)


def aligned(O):
    """For each text word, the OCR word's marks where the words agree."""
    sm = difflib.SequenceMatcher(None, [w for w, _, _ in T], [w for w, _ in O], autojunk=False)
    got = {}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                got[i1 + k] = O[j1 + k][1]
    return got


ga, gb = aligned(A), aligned(B)
n = 0
for i, (w, m, page) in enumerate(T):
    if i in ga and i in gb and ga[i] == gb[i] and ga[i] != m:
        n += 1
        ctx = " ".join(x[0] + x[1] for x in T[max(0, i - 4) : i + 1])
        print(f"p.{page:>3}  text[{m}]  ocr[{ga[i]}]   …{ctx} _ {' '.join(x[0] for x in T[i + 1 : i + 3])}…")
print(f"{n} places", file=sys.stderr)
