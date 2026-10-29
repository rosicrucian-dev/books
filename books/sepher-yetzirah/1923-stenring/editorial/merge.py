# Merges the two readings of each page into one (ocr/merged/NN.txt),
# Markdown, a paragraph a block: Tesseract's words (ocr/tsv/NN.tsv,
# eng_best) are the base, for their paragraphs, dashes, quotation marks, æ
# and accents, which Google's text layer loses, and for their places on the
# page (italic.py: the slant of each word's strokes, which neither reading
# records); their spelling is corrected from Google's (ocr/google/), which
# reads the type's small capitals, its c and e, and its digits better:
#
# - digits: Google's (Tesseract reads this type's 3 as 8);
# - a word: Google's where Google's is a word (the dictionary, or the
#   book's own vocabulary) and Tesseract's is not; the print's æ; small
#   capitals; a word Google joins or splits;
# - anything else: Tesseract's, listed in review.txt to be read on the
#   page (look.py) and settled in edits.json.
#
# Hebrew is not read here: Tesseract cannot, and Google's is checked
# against Stenring's transliterations (hebrew.py).
#
#   python3 merge.py [first last]

import csv
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from italic import score  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "ocr" / "merged"
OUT.mkdir(exist_ok=True)
DICT = set(w.strip().lower() for w in open("/usr/share/dict/words"))
WORD = re.compile(r"[A-Za-zÀ-ÿæœÆŒ]+|\d+")
ITALIC = 0.99  # the italic shear's score against the upright's (italic.py)

book = Counter()
for f in (HERE / "ocr" / "google").glob("*.txt"):
    for w in WORD.findall(f.read_text()):
        book[w.lower()] += 1
VOCAB = {w for w, n in book.items() if n > 1} | DICT


def known(w):
    return w.lower() in VOCAB or w.lower().rstrip("s") in VOCAB


def quotes(text):
    """Tesseract reads this type's quotation marks as asterisks ("**", "*“",
    "‘*“"): never a mark of the print's own. At a word's start, an opening
    mark; at its end, a closing one; alone, an opening one."""
    if re.fullmatch(r"[*‘’“”\"']+", text) and "*" in text:
        return "“"
    text = re.sub(r"^[‘“\"']*\*[*‘“\"']*", "“", text)
    text = re.sub(r"[’”\"']*\*[*’”\"']*$", "”", text)
    return text


def tess_words(n):
    im = np.array(Image.open(HERE / "pages" / f"p-{n:02d}.png").convert("L")) < 128
    out = []
    for r in csv.DictReader(open(HERE / "ocr/tsv" / f"{n:02d}.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not r["text"].strip():
            continue
        l, t, w, h = (int(r[k]) for k in ("left", "top", "width", "height"))
        text = quotes(r["text"])
        # A word joined to the next by a dash ("worlds—Olam") is judged in
        # its parts, its box shared out by their letters: the one may be
        # roman, the other italic.
        parts = re.findall(r"[^—]+—?|—", text) if re.search(r"\w—\w", text) else [text]
        x = l
        for k, part in enumerate(parts):
            pw = round(w * len(part) / len(text)) if k < len(parts) - 1 else l + w - x
            crop = im[t : t + h, x : x + pw]
            letters = sum(c.isalpha() for c in part)
            it = None
            if letters >= 1 and h > 10 and crop.any():
                s0 = score(crop, 0.0)
                it = s0 > 0 and score(crop, 0.22) / s0 >= ITALIC
            out.append(dict(text=part, par=(r["block_num"], r["par_num"]), line=(r["block_num"], r["par_num"], r["line_num"]), italic=it, left=x, joined=k > 0))
            x += pw
    return out


a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 81)
review = []
for n in range(a, b + 1):
    W = tess_words(n)
    g = (HERE / "ocr" / "google" / f"{n:03d}.txt").read_text()
    g = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", g)
    G = WORD.findall(re.sub(r"[֐-׿]+", " ", g))
    # Each word's alphanumeric pieces, pointing back to the word.
    T = []
    for k, w in enumerate(W):
        for m in WORD.finditer(w["text"]):
            T.append([k, m.start(), m.end(), m.group()])
    sm = difflib.SequenceMatcher(None, [x[3].lower() for x in T], [w.lower() for w in G], autojunk=False)
    subs = []  # (piece index, new text) ; (first, last, new) for runs
    quote_before = set()  # words an opening quotation mark goes before

    def put(i, new):
        subs.append((i, i, new))

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        tw = [x[3] for x in T[i1:i2]]
        gw = G[j1:j2]
        if op == "equal":
            for k in range(i2 - i1):
                if tw[k] != gw[k]:
                    put(i1 + k, gw[k])
            continue
        settled = False
        if op == "replace" and len(tw) == len(gw):
            new = []
            for x, y in zip(tw, gw):
                if x.isdigit() and y.isdigit():
                    new.append(y)
                elif re.search(r"[æœÆŒ]", y) and y.lower().replace("æ", "ae").replace("œ", "oe").replace("ae", "e") == x.lower().replace("ae", "e"):
                    new.append(y)
                elif len(y) > 1 and y.isupper() and not x.isupper() and not x.islower():
                    new.append(y)
                elif known(y) and not known(x):
                    new.append(y)
                elif known(x) and not known(y):
                    new.append(x)
                elif x.lower() == y.lower():
                    new.append(y)
                else:
                    new = None
                    break
            if new is not None:
                for k, y in enumerate(new):
                    if y != tw[k]:
                        put(i1 + k, y)
                settled = True
        elif op == "replace" and len(tw) == 1 and len(gw) == 2 and tw[0].lower().replace("ae", "") == (gw[0] + gw[1]).lower():
            settled = True  # Google splits a word at its æ
        elif op == "replace" and len(tw) == 2 and len(gw) == 1 and (tw[0] + tw[1]).lower() == gw[0].lower():
            if W[T[i1][0]]["line"] == W[T[i2 - 1][0]]["line"]:
                subs.append((i1, i2 - 1, gw[0]))
            settled = True  # (across a line's end, extract.py joins it)
        elif op == "replace" and len(tw) == 1 and len(gw) == 1 and re.search(r"[æœÆŒ]", gw[0]):
            put(i1, gw[0])
            settled = True
        elif op == "replace" and all(w.isupper() and len(w) > 1 for w in gw) and not any(w.isupper() for w in tw) and abs(len("".join(tw)) - len("".join(gw))) <= 3:
            subs.append((i1, i2 - 1, " ".join(gw)))
            settled = True  # a phrase in small capitals
        elif op == "insert" and all(w in ("66", "99") for w in gw):
            # Google's reading of a quotation mark: an opening one, where
            # Tesseract has none, goes before the next word.
            if "66" in gw and i1 < len(T):
                k = T[i1][0]
                if not re.match(r"[“‘\"']", W[k]["text"]) and not (k > 0 and W[k - 1]["text"] in ("“",)):
                    quote_before.add(k)
            settled = True
        if not settled:
            ctx = " ".join(x[3] for x in T[max(0, i1 - 4):i1])
            review.append(f"pdf{n:>3}  tess[{' '.join(tw)}]  google[{' '.join(gw)}]   …{ctx} _ {' '.join(x[3] for x in T[i2:i2 + 3])}…")
    # Apply, within each word (from the end, so the offsets hold).
    texts = [w["text"] for w in W]
    for k in quote_before:
        texts[k] = "“" + texts[k]
    for i1, i2, new in sorted(subs, key=lambda s: (T[s[0]][0], T[s[0]][1]), reverse=True):
        k1, s1 = T[i1][0], T[i1][1]
        k2, e2 = T[i2][0], T[i2][2]
        if k1 == k2:
            texts[k1] = texts[k1][:s1] + new + texts[k1][e2:]
        else:
            texts[k1] = texts[k1][:s1] + new + texts[k2][e2:]
            for k in range(k1 + 1, k2 + 1):
                texts[k] = ""
    # Lines into paragraphs; italic runs marked.
    out, cur_par, cur_line, line = [], None, None, []

    def flush():
        if line:
            out.append(line_text(line))

    def line_text(ws):
        s, run = "", False
        for t, it, joined in ws:
            if not t:
                continue
            m = re.match(r"^([(\[“‘\"']*)(.*?)([)\].,;:!?”’\"'—]*)$", t)
            pre, core, post = m.groups()
            sp = "" if joined else (" " if s else "")
            if it and core and not run:
                s += sp + pre + "*" + core
                run = True
            elif it and core:
                s += sp + pre + core
            elif run:
                s += "*" + sp + t
                run = False
            else:
                s += sp + t
            if run and post:
                s += "*" + post
                run = False
        if run:
            s += "*"
        return s

    # The text's left margin: where most lines begin. A line set in from it
    # (a paragraph's first, a heading, a verse) is marked "¶ ".
    starts = {}
    for w in W:
        starts.setdefault(w["line"], w["left"])
    lefts = sorted(starts.values())
    margin = lefts[len(lefts) // 5] if lefts else 0
    for w, t in zip(W, texts):
        if w["line"] != cur_line:
            flush()
            line = []
            if w["par"] != cur_par and out:
                out.append("")
            cur_par = w["par"]
            if starts[w["line"]] > margin + 25:
                line.append(("¶", False, False))
        cur_line = w["line"]
        line.append((t, bool(w["italic"]), w.get("joined", False)))
    flush()
    (OUT / f"{n:02d}.txt").write_text("\n".join(out) + "\n")
(HERE / f"review.txt").write_text("\n".join(review) + "\n")
print(len(review), "places to read")
