# Reads the Letters (cloud.txt, the 1909 text from sacred-texts, or
# cloud-edited.txt) against the translation's first printing, in The
# Unknown World, January–June 1895, a Letter an issue, in two readings: the
# OCR of the IAPSOP scans (source/unknown-world-1895/*.txt) and adepti.com's
# transcription of the magazine (source/adepti-1895.txt). A word of the text
# that neither agrees with is printed, with its page and context, to be read
# on the 1895 scan (look.py) and decided: a slip of the 1909 transcription
# (edits.json), or the 1909 revision's own wording (kept). Waite's
# Introduction is not in the magazine and has no second reading.
#
#   python3 compare.py [cloud.txt]

import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cloud.txt"
ISSUES = ["v1_n6_jan_15_1895", "v2_n1_feb_15_1895", "v2_n2_mar_15_1895", "v2_n3_apr_15_1895", "v2_n4_may_15_1895", "v2_n5_jun_15_1895"]


def toks(s):
    return re.findall(r"[A-Za-zÀ-ÿæœ]+|\d+", s)


def key(w):
    return w.lower().replace("æ", "ae").replace("œ", "oe")


letters = []  # [(words, pages)]
for line in path.read_text().splitlines():
    tag, _, body = line.partition("\t")
    if tag == "@part":
        letters.append(([], [], body))
        continue
    if tag == "@note" or not letters:
        continue
    for w in toks(re.sub(r"\[\^\d+\]", " ", body)):
        letters[-1][0].append(w)
        letters[-1][1].append(tag[1:])
letters = [l for l in letters if l[2].startswith("Letter")]

adepti = (HERE / "source/adepti-1895.txt").read_text()
adepti = re.sub(r"-\s*\n\s*", "", adepti)
# adepti's letters, by their heads.
heads = [m.start() for m in re.finditer(r"^\s*LETTER [IVX]+", adepti, re.M)]
adepti_parts = [adepti[a:b] for a, b in zip(heads, heads[1:] + [len(adepti)])]


def differing(text, other):
    B = toks(other)
    sm = difflib.SequenceMatcher(None, [key(w) for w in text], [key(w) for w in B], autojunk=False)
    bad, extra = set(), {}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("replace", "delete"):
            bad.update(range(i1, i2))
        if op in ("replace", "insert"):
            extra[i1] = " ".join(B[j1:j2])
    return bad, extra


n = 0
for k, (text, pages, label) in enumerate(letters):
    ocr = (HERE / "source/unknown-world-1895" / f"{ISSUES[k]}.txt").read_text()
    ocr = re.sub(r"-\s*\n\s*", "", ocr)
    # The Letter's run in the issue: from where its first words are (the
    # best match of its first six), as long again and half.
    words = toks(ocr)
    first = [key(w) for w in text[:6]]
    best = max(range(len(words) - 6), key=lambda i: sum(key(w) == f for w, f in zip(words[i : i + 6], first)))
    ocr = " ".join(words[max(0, best - 20) : best + int(len(text) * 1.5)])
    bad_o, extra_o = differing(text, ocr)
    bad_a, extra_a = differing(text, adepti_parts[k] if k < len(adepti_parts) else "")
    both = sorted(bad_o & bad_a)
    print(f"== {label}: {len(text)} words")
    i = 0
    while i < len(both):
        a = b = both[i]
        while i + 1 < len(both) and both[i + 1] == b + 1:
            i += 1
            b = both[i]
        i += 1
        n += 1
        print(f"p.{pages[a]:>3}  text[{' '.join(text[a:b + 1])}]  1895ocr[{extra_o.get(a, '')[:40]}]  adepti[{extra_a.get(a, '')[:40]}]   …{' '.join(text[max(0, a - 5):a])} _ {' '.join(text[b + 1:b + 4])}…")
    for j in sorted(set(extra_o) & set(extra_a)):
        if j in bad_o or j in bad_a:
            continue
        x, y = extra_o[j].lower().split(), extra_a[j].lower().split()
        if set(x) & set(y):
            n += 1
            print(f"p.{pages[min(j, len(pages) - 1)]:>3}  text[]  1895ocr[{extra_o[j][:40]}]  adepti[{extra_a[j][:40]}]   …{' '.join(text[max(0, j - 5):j])} _ {' '.join(text[j:j + 3])}…")
print(f"{n} places", file=sys.stderr)
