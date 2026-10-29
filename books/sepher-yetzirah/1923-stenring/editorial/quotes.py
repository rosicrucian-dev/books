# quotes.py FILE…: Tesseract's opening double quotation marks, read as
# ‘, ‘“, ““ or ‘““, made one “: a run of opening marks is one; a ‘ whose
# closing mark is ” is “; a stray ’ after ” goes. Single quotations (‘…’)
# stand. Applied to the drafts before they are proofread.
import re, sys
from pathlib import Path


def fix(t):
    t = re.sub(r"[‘“]{2,}", "“", t)
    t = t.replace("”’", "”")
    out = list(t)
    for i, c in enumerate(out):
        if c != "‘" or (i > 0 and out[i - 1].isalpha() and i + 1 < len(out) and out[i + 1].isalpha()):
            continue
        rest = "".join(out[i + 1 :])
        m = re.search(r"[’”]", rest)
        if m and m.group() == "”":
            out[i] = "“"
    return "".join(out)


for f in sys.argv[1:]:
    p = Path(f)
    lines = p.read_text().split("\n")
    p.write_text("\n".join(l.split("\t", 1)[0] + "\t" + fix(l.split("\t", 1)[1]) if "\t" in l else l for l in lines))
