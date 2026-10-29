# The Kybalion (Chicago: The Yogi Publication Society, 1908), from the
# Wikisource transcription of the 1908 printing, page by page
# (source/wikisource/NNN.wiki, the scan's pages; every page of text
# proofread there), as Markdown paragraphs, one per line, each tagged with
# its page (the print's page number):
#
#   @<page>\t<text>
#
# and "@part\t<label>" where a part of the book begins (the Introduction,
# each chapter). Italic is kept as *…*. The Kybalion's sayings, set in
# smaller type, are quotations (> …); lists set line under line are one
# paragraph, a line each (<br />). Running heads and page numbers are the
# pages' own (<noinclude>) and left out; a word hyphenated across a page
# is whole. The title page, its back, the dedication and the contents are
# the book's record, not text.
#
#   python3 extract.py > kybalion.txt

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PAGES = HERE / "source" / "wikisource"
FIRST, LAST = 11, 232  # the Introduction's first page (printed 7), the last
OFFSET = 4  # scan page − printed page
ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV".split()


def strip(s):
    """A template's text: {{name|text}} → text, innermost first."""
    while True:
        t = re.sub(r"\{\{(?:c|sc|asc|smaller|sm|x-smaller|larger|right|center)\|([^{}]*)\}\}", r"\1", s)
        t = re.sub(r"\{\{gap\|[^{}]*\}\}", "", t)
        t = re.sub(r"\{\{wsp1\}\}", " ", t)
        # {{ditto|width|text|…}}: the text, set in the width of another (a
        # list's numbers, aligned).
        t = re.sub(r"\{\{ditto\|[^|{}]*\|?([^|{}]*)(\|[^{}]*)?\}\}", r"\1", t)
        t = re.sub(r"\{\{SIC\|([^|{}]*)\|[^{}]*\}\}", r"\1", t)  # as printed
        if t == s:
            return t
        s = t


def body(n):
    s = (PAGES / f"{n:03d}.wiki").read_text(encoding="utf-8")
    s = re.sub(r"<noinclude>.*?</noinclude>", "", s, flags=re.S)
    # A word broken across the page: whole where it starts, gone where it
    # ends.
    s = re.sub(r"\{\{hws\|[^|{}]*\|([^|{}]*)(\|[^{}]*)?\}\}", r"\1", s)
    s = re.sub(r"\{\{hwe\|[^{}]*\}\}", "", s)
    # A line's end hyphen left in a line ("uncov- ered", fifteen times, each
    # an ordinary word, whole in the print's OCR and in Gutenberg's): whole.
    s = re.sub(r"([A-Za-z])- +([a-z])", r"\1\2", s)
    return s


# The pages run together; a paragraph that ends with a page is marked
# {{nop}} there.
pieces = []
for n in range(FIRST, LAST + 1):
    s = body(n).strip()
    if not s:
        continue
    pieces.append((n - OFFSET, s))

text = ""
marks = []  # (offset in text, page)
for page, s in pieces:
    s = s.replace("{{nop}}", "\n\n").replace("{{dhr}}", "\n\n")
    if s.startswith("{{c|"):  # a chapter's head: a page of its own
        text = text.rstrip() + "\n\n"
    # A word broken at the page's end with no template for it (twenty
    # times, every one an ordinary word: "explana-" "tion"): whole.
    if re.search(r"[A-Za-z]-$", text) and re.match(r"[a-z]", s):
        text = text[:-1]
    elif text and not text.endswith("\n\n"):
        text += " "
    marks.append((len(text), page))
    text += s

# A proofreader's note (one, across a page: "<!--(:-->") is not text.
text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
# The heads: "INTRODUCTION." or "CHAPTER N." and its title, centred.
text = re.sub(r"\{\{c\|(INTRODUCTION\.|CHAPTER [IVXL]+\.)\s*(.*?)\}\}\s*(?=\n|$)", lambda m: "\n\n\x04" + m.group(1) + "\x05" + " ".join(m.group(2).split()) + "\n\n", text, flags=re.S)
def lines(s, mark):
    """Lines set one under another: one paragraph, a line each."""
    return " <br />\n".join(l.strip().lstrip(mark).strip() for l in s.strip().splitlines() if l.strip())


def blocks(text, name, make):
    """Each {{name|…}}, its braces balanced, replaced by make(its text)."""
    out, i = "", 0
    while (j := text.find("{{" + name + "|", i)) >= 0:
        k, depth = j, 0
        while True:
            if text.startswith("{{", k):
                depth, k = depth + 1, k + 2
            elif text.startswith("}}", k):
                depth, k = depth - 1, k + 2
                if depth == 0:
                    break
            else:
                k += 1
        out += text[i:j] + make(text[j + len(name) + 3 : k - 2])
        i = k
    return out + text[i:]


# The sayings, set smaller: quotations. A line centred over one ("I. THE
# PRINCIPLE OF MENTALISM.", Chapter II's Seven Principles) is a heading.
def saying(s):
    m = re.match(r"\s*\{\{c\|([^{}]*)\}\}\s*(.*)", s, flags=re.S)
    head = "\n\n\x08" + m.group(1).strip() + "\n\n" if m else ""
    return head + "\n\n\x01" + lines(m.group(2) if m else s, ":") + "\x02\n\n"


text = blocks(text, "smaller block", saying)
# Lists set line under line ({{hi/s}} … {{hi/e}}, {{plainlist|* …}}).
# (A list carried over a page goes on at its next ":" item.)
text = re.sub(r"\{\{hi/s\}\}(.*?)\{\{hi/e\}\}", lambda m: "\n\n" + lines(re.sub(r"\s+:", "\n:", m.group(1)), ":") + "\n\n", text, flags=re.S)
text = blocks(text, "plainlist", lambda s: "\n\n" + lines(s, "*") + "\n\n")


# Each paragraph's page: the page its first words are on (the pages'
# words, in order, each with its page).
WORDS = [(w.lower(), pg) for pg, s in pieces for w in re.findall(r"[A-Za-z]+", strip(re.sub(r"\{\{(rh|dhr|nop|hwe)[^{}]*\}\}", " ", s)))]
seen = 0


def page_at(para):
    global seen
    first = [w.lower() for w in re.findall(r"[A-Za-z]+", strip(para))][:6]
    for i in range(seen, len(WORDS) - len(first) + 1):
        if [w for w, _ in WORDS[i : i + len(first)]] == first:
            seen = i + 1
            return WORDS[i][1]
    return WORDS[min(seen, len(WORDS) - 1)][1]


out = []
pos = 0
for para in re.split(r"\n\s*\n", text):
    start = text.index(para, pos) if para else pos
    pos = start + len(para)
    para = para.strip()
    if not para:
        continue
    page = page_at(para)
    head = re.fullmatch(r"\x04(INTRODUCTION\.|CHAPTER [IVXL]+\.)\x05(.*)", para, flags=re.S)
    if head:
        # Numbered in order: the transcription's heads are typed, and one is
        # wrong (Chapter VII's, typed "CHAPTER V.").
        label = "Introduction" if head.group(1).startswith("INTRO") else f"Chapter {ROMAN[sum(1 for l in out if l.startswith('@part')) - 1]}"
        if head.group(1).rstrip(".").title() != label.title():
            print(f"page {page}: the transcription heads it {head.group(1)!r}; it is {label}", file=sys.stderr)
        out.append(f"@part\t{label}")
        if head.group(2):
            out.append(f"@{page}\t## {strip(head.group(2)).strip()}")
        continue
    if para.startswith("\x08"):
        out.append(f"@{page}\t### {strip(para[1:]).strip()}")
        continue
    # A saying set smaller ({{smaller block|…}} or {{smaller|…}}, the whole
    # paragraph) is a quotation.
    if re.fullmatch(r"\{\{smaller\|.*\}\}", para, flags=re.S) and para.count("{{smaller|") == 1:
        para = "\x01" + para[10:-2] + "\x02"
    quote = para.startswith("\x01")
    para = para.strip("\x01\x02")
    s = strip(para)
    s = re.sub(r"'''(.*?)'''", r"**\1**", s)
    s = re.sub(r"''(.*?)''", r"*\1*", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *(?!<)", " ", s.replace(" <br />\n", "\x03")).replace("\x03", " <br />\n").strip()
    if "{{" in s or "}}" in s or "[[" in s:
        where = re.search(r".{0,80}(\{\{|\}\}|\[\[).{0,80}", s, re.S).group()
        raise SystemExit(f"page {page}: markup left: {where!r}")
    if quote:
        s = "> " + s.replace("\n", "\n> ")
    out.append(f"@{page}\t{s}" if "\n" not in s else f"@{page}\t" + s.replace("\n", "\\n"))

print("\n".join(out))
