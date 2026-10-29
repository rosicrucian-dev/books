# Compares a manifesto's text (fama.txt / confessio.txt, or the built
# .mdx) with the OCR of the 1887 printing (source/scan-ocr.txt, archive.org
# realhistoryofros00wait), word by word, and prints every place they
# differ, with context. OCR noise is expected; what the transcription
# lacks or has wrong shows here too, and is decided in edits.json.
#
#   python3 compare.py fama fama.txt

import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SPAN = {
    "fama": ("Seeing  the  only  wise", "Sub  umbra  alarum"),
    "confessio": ("Here,  gentle  reader", "Fraternitas  R.  C."),
}
which, path = sys.argv[1], sys.argv[2]
ocr = (HERE / "source/scan-ocr.txt").read_text()
a, b = SPAN[which]
start = ocr.index(a)
ocr = ocr[start : ocr.index(b, start) + 40]
# Running heads, page numbers, line-end hyphens.
ocr = re.sub(r"^.*(HISTORY OF THE ROSICRUCIANS|THE FAMA FRATERNITATIS|THE CONFESSIO FRATERNITATIS|CONFESSIO FRATERNITATIS|FAMA FRATERNITATIS)\.?\s*\d*\s*$", "", ocr.replace("  ", " "), flags=re.M | re.I)
ocr = re.sub(r"-\s*\n\s*", "", ocr)

text = Path(path).read_text()
text = re.sub(r"^@\S+\t", "", text, flags=re.M)
text = re.sub(r"\[\^\d+\]", "", text)


def toks(s):
    return re.findall(r"[A-Za-zÀ-ÿæœÆŒ]+|\d+", s)


def key(w):
    return w.lower().replace("æ", "ae").replace("œ", "oe")


A, B = toks(text), toks(ocr)
sm = difflib.SequenceMatcher(None, [key(w) for w in A], [key(w) for w in B], autojunk=False)
n = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "equal":
        continue
    n += 1
    ctx = " ".join(A[max(0, i1 - 5) : i1])
    after = " ".join(A[i2 : i2 + 4])
    print(f"{op:7} text[{' '.join(A[i1:i2])}]  scan[{' '.join(B[j1:j2])}]   …{ctx} _ {after}…")
print(f"{n} differences; {len(A)} words in text, {len(B)} in scan", file=sys.stderr)
