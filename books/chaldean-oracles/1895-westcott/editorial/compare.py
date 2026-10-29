# Reads the text (oracles.txt, from sacred-texts) against two readings of
# the 1895 scan (source/scan.pdf, IAPSOP), word by word: Tesseract's
# (ocr/tess/NN.txt) and the scan's own text layer (source/scan-text.txt,
# Acrobat Paper Capture). A word of the text that neither agrees with is
# printed, with its page and context, to be read on the scan (look.py) and
# decided in edits.json; so is a run of words both have and the text lacks.
# Each note is read at the foot of the page its mark is on, as printed.
#
#   python3 compare.py [oracles-edited.txt]

import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "oracles.txt"


def toks(s):
    return re.findall(r"[A-Za-zæÆœŒéèëÉË]+|\d+", s)


def key(w):
    """A word as both readings can match it: the OCR reads æ and œ as
    "ae", "e", "z", "s", "c" in any order, and drops a dieresis; a word with
    æ or œ is matched without those letters."""
    w = w.lower().replace("é", "e").replace("è", "e").replace("ë", "e")
    if re.search(r"[æœ]", w):
        return "~" + re.sub(r"[æœaezsc]", "", w)
    return w


blocks, notes = [], {}
for line in path.read_text().splitlines():
    tag, _, body = line.partition("\t")
    if tag == "@part":
        continue
    if tag == "@note":
        m = re.match(r"\[\^(\d+)\]: (.*)", body)
        notes[m.group(1)] = m.group(2)
        continue
    blocks.append([tag[1:], re.sub(r"<[^>]+>|\\n|\{\{table \d+\}\}", " ", body)])
# A note after the last block of its mark's page.
for n, note in notes.items():
    at = max(i for i, (p, b) in enumerate(blocks) if f"[^{n}]" in b)
    page = blocks[at][0]
    while at + 1 < len(blocks) and blocks[at + 1][0] == page:
        at += 1
    blocks.insert(at + 1, [page, note])

text, pages = [], []
for page, b in blocks:
    for w in toks(re.sub(r"\[\^\d+\]", " ", b)):
        text.append(w)
        pages.append(page)


def ocr_pages(pages_text):
    out = []
    for t in pages_text:
        lines = t.splitlines()
        # the running number, a line alone at the head
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and re.fullmatch(r"\s*[\dIlO]{1,2}\s*", lines[0]):
            lines.pop(0)
        out.append("\n".join(lines))
    s = "\n".join(out)
    return re.sub(r"(\w)-\s*\n\s*", r"\1", s)  # words broken at a line's end


tess = ocr_pages((HERE / "ocr/tess" / f"{n:02d}.txt").read_text() for n in range(3, 55))
layer = ocr_pages((HERE / "source/scan-text.txt").read_text().split("\f")[2:54])


def differing(other):
    B = toks(other)
    A = [key(w) for w in text]
    # an OCR word matches a text word with æ if it does so without those letters
    # and is not itself a word of the text ("one" is not "Æon")
    ae, plain = {k for k in A if k.startswith("~")}, set(A)

    def bkey(w):
        k, loose = key(w), "~" + re.sub(r"[aezsc]", "", key(w))
        return loose if k not in plain and loose in ae else k

    Bk = [bkey(w) for w in B]
    sm = difflib.SequenceMatcher(None, A, Bk, autojunk=False)
    bad, extra = set(), {}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("replace", "delete"):
            bad.update(range(i1, i2))
        if op in ("replace", "insert"):
            extra[i1] = " ".join(B[j1:j2])
    return bad, extra


bad_t, extra_t = differing(tess)
bad_l, extra_l = differing(layer)

n = 0
both = sorted(bad_t & bad_l)
k = 0
while k < len(both):
    i = j = both[k]
    while k + 1 < len(both) and both[k + 1] == j + 1:
        k += 1
        j = both[k]
    k += 1
    n += 1
    print(f"p.{pages[i]:>3}  text[{' '.join(text[i:j + 1])}]  tess[{extra_t.get(i, '')[:40]}]  layer[{extra_l.get(i, '')[:40]}]   …{' '.join(text[max(0, i - 5):i])} _ {' '.join(text[j + 1:j + 4])}…")
for i in sorted(set(extra_t) & set(extra_l)):
    a, b = extra_t[i].lower().split(), extra_l[i].lower().split()
    # (a run beside a word already listed is listed too, if it is long: a
    # passage the text lacks)
    if (i in bad_t or i in bad_l) and min(len(a), len(b)) < 4:
        continue
    if set(a) & set(b):
        n += 1
        print(f"p.{pages[min(i, len(pages) - 1)]:>3}  text[]  tess[{extra_t[i][:40]}]  layer[{extra_l[i][:40]}]   …{' '.join(text[max(0, i - 5):i])} _ {' '.join(text[i:i + 3])}…")
print(f"{n} places; {len(text)} words in the text", file=sys.stderr)
