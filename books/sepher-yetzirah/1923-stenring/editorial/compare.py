# The two readings of the scan, word by word, page by page: Google's text
# layer (ocr/google/NNN.txt) and Tesseract's (ocr/tess/NN.txt, eng_best).
# Every place they differ is printed with its context, to be read on the
# page (look.py) and settled in edits.json. Hebrew is left out here (it is
# checked against its transliteration, hebrew.py), and so is punctuation
# but the dash (a hyphen in one, a dash in the other, is a place to read).
#
#   python3 compare.py [first last]

import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (10, 76)


def toks(s):
    s = re.sub(r"[֐-׿‎‏‪-‮]+", " ", s)
    s = re.sub(r"-\s*\n\s*", "", s)  # a line's end
    return re.findall(r"[A-Za-z0-9]+|[—–]", s)


n = 0
for p in range(a, b + 1):
    g = HERE / "ocr/google" / f"{p:03d}.txt"
    t = HERE / "ocr/tess" / f"{p:02d}.txt"
    if not g.exists() or not t.exists():
        continue
    A, B = toks(g.read_text()), toks(t.read_text())
    sm = difflib.SequenceMatcher(None, [w.lower() for w in A], [w.lower() for w in B], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        n += 1
        print(f"pdf{p:>3}  google[{' '.join(A[i1:i2])}]  tess[{' '.join(B[j1:j2])}]   …{' '.join(A[max(0, i1 - 4):i1])} _ {' '.join(A[i2:i2 + 3])}…")
print(f"{n} places", file=sys.stderr)
