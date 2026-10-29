# The Hebrew. Stenring prints each Hebrew word with his transliteration of
# it ("אלכסון = ALKSVNf"), letter for letter by his Table I: A א, B ב, G ג,
# D ד, H ה, V ו, Z ז, Ch ח, T ט, I י, K כ, L ל, M מ, N נ, S ס, O ע, P פ,
# Tz צ, Q ק, R ר, Sh ש, Th ת; "f" after K, M, N, P, Tz: the final form (ך ם
# ן ף ץ). Tesseract cannot read the Hebrew; Google's text layer reads most
# of it. Each pair Google reads is checked: its Hebrew against the Hebrew
# its transliteration spells. Where they agree, the word is settled; where
# they do not, or Google has no Hebrew, it is read on the page (look.py)
# and settled in edits.json.
#
#   python3 hebrew.py [first last]     the pairs, by page, and their state

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
KEY = [("Tzf", "ץ"), ("Tz", "צ"), ("Sh", "ש"), ("Th", "ת"), ("Ch", "ח"), ("Kf", "ך"), ("Mf", "ם"), ("Nf", "ן"), ("Pf", "ף"),
       ("A", "א"), ("B", "ב"), ("G", "ג"), ("D", "ד"), ("H", "ה"), ("V", "ו"), ("Z", "ז"), ("T", "ט"), ("I", "י"), ("K", "כ"),
       ("L", "ל"), ("M", "מ"), ("N", "נ"), ("S", "ס"), ("O", "ע"), ("P", "פ"), ("Q", "ק"), ("R", "ר")]
FINAL = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}
HEB = re.compile(r"[א-ת]+")
GEMATRIA = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]))
GEMATRIA.update({"ך": 20, "ם": 40, "ן": 50, "ף": 80, "ץ": 90})


def spell(translit):
    """The Hebrew a transliteration spells, word by word (its spaces kept);
    None if it is not one."""
    words = []
    for w in translit.split():
        out, i = "", 0
        while i < len(w):
            for k, h in KEY:
                if w.startswith(k, i):
                    out += h
                    i += len(k)
                    break
            else:
                return None
        words.append(out)
    return " ".join(words)


def letters(h):
    """Hebrew without spaces, final forms as the print writes them."""
    return re.sub(r"\s+", "", h)


def gematria(h):
    return sum(GEMATRIA.get(c, 0) for c in h)


def google_pairs(n):
    """Google's Hebrew words on a PDF page, each with the transliteration
    after its "=", in the page's order."""
    t = (HERE / "ocr" / "google" / f"{n:03d}.txt").read_text()
    t = re.sub(r"[‎‏‪-‮]", "", t)
    pairs = []
    for line in t.splitlines():
        # "= טלה TLH": the Hebrew, visually after its "=" in Google's line,
        # then the transliteration.
        for m in re.finditer(r"([א-ת][א-ת \"'״׳-]*)\s*=?\s*=?\s*([A-Z][A-Za-z]*(?:\s[A-Z][A-Za-z]*)*)", line):
            heb = m.group(1).strip()
            tr = m.group(2).strip()
            pairs.append((heb, tr))
    return pairs


if __name__ == "__main__":
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (10, 76)
    for n in range(a, b + 1):
        for heb, tr in google_pairs(n):
            sp = spell(tr)
            ok = sp is not None and letters(sp) == letters(heb)
            # Google gives the Hebrew in visual order on some lines.
            rev = sp is not None and letters(sp) == letters(heb)[::-1]
            state = "ok" if ok else "reversed" if rev else "CHECK"
            print(f"pdf{n:>3}  {state:8}  {heb}  =  {tr}   spells {sp}")


# ---------------------------------------------------------------------------
# Setting the Hebrew into the text (extract.py's paragraphs).

PDF = lambda printed: printed + 5 if printed <= 14 else printed + 7 if printed <= 24 else printed + 9  # extract.PRINTED reversed
# "<junk> = TRANSLIT": what Tesseract leaves where the Hebrew stood, then
# the transliteration (letters of the key, in words, an "f" for a final).
SLOT = re.compile(r"(?:(?<=\s)|^)([^\s=]*)\s*=\s*((?:(?:Tzf|Tz|Sh|Th|Ch|Kf|Mf|Nf|Pf|[ABGDHVZTIKLMNSOPQR])+(?:\s+|(?=[\s.,;:)!?(\]—-]|$)))+)")
ENGLISH = set(w.strip().lower() for w in open("/usr/share/dict/words"))


def junk(tok):
    """Is this what Tesseract leaves for Hebrew (not a word of the text)?"""
    core = re.sub(r"[^\w]", "", tok)
    if not core:
        return True
    if HEB.search(tok):
        return True
    return core.lower() not in ENGLISH or len(core) <= 2


import json  # noqa: E402

READ = json.loads((HERE / "hebrew-read.json").read_text()) if (HERE / "hebrew-read.json").exists() else []


def _norm(tr):
    return re.sub(r"\s+", "", tr or "").lower()


def set_hebrew(page, text, used, checks):
    """Puts each slot's Hebrew in, in the page's order, from Google's pairs
    on the page (and the next, for a paragraph running over): the closest of
    the next few unused, by spelling and transliteration. Where its Hebrew
    agrees with a transliteration (ours or Google's) it is set; otherwise
    the slot is marked ⟦…⟧ and noted in checks, to be read on the page."""
    from difflib import SequenceMatcher as SM
    pairs = [(PDF(page) + d, i, h, t) for d in (0, 1) for i, (h, t) in enumerate(google_pairs(PDF(page) + d))]

    def fix(m):
        tok, tr = m.group(1), m.group(2).strip()
        tail = " " if m.group(2).endswith(" ") else ""
        if not junk(tok):
            return m.group(0)
        for r in READ:
            if r["page"] == page and re.sub(r"\s+", "", r.get("ours", r["translit"])) == re.sub(r"\s+", "", tr):
                return f"{r['hebrew']} = {r['translit']}{tail}"
        mine = spell(tr)
        free = [p for p in pairs if (p[0], p[1]) not in used][:4]
        best, at = 0, None
        for p in free:
            _, _, h, gtr = p
            r = max(SM(None, letters(mine or ""), letters(h)).ratio(), SM(None, _norm(tr), _norm(gtr)).ratio())
            if r > best:
                best, at = r, p
        if at and best >= 0.6:
            pn, i, h, gtr = at
            used.add((pn, i))
            if mine and letters(mine) == letters(h):
                return f"{h} = {tr}{tail}"
            gsp = spell(gtr)
            if gsp and letters(gsp) == letters(h):
                checks.append(f"p.{page}  translit: ours {tr!r}, Google's {gtr!r} agrees with {h}")
                return f"{h} = {gtr}{tail}"
            checks.append(f"p.{page}  DISAGREE  Google {h} = {gtr}; ours = {tr} (spells {mine})")
            return f"⟦{h}|{mine or '?'}⟧ = {tr}{tail}"
        checks.append(f"p.{page}  NO HEBREW  [{tok}] = {tr}   (spells {mine})")
        return f"⟦{mine or '?'}⟧ = {tr}{tail}"

    return SLOT.sub(fix, text)
