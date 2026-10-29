# The Chaldæan Oracles of Zoroaster, edited and revised by Sapere Aude (W.
# Wynn Westcott), with an introduction by L. O. (Percy Bullock); Collectanea
# Hermetica, Volume VI (London: Theosophical Publishing Society, 1895), from
# the sacred-texts.com transcription of it (source/sacred-texts/coz01.htm …
# coz08.htm, John Bruno Hare, 2006, from his own copy; fetched from a
# mirror, sacred-texts refusing scripts), as Markdown blocks, one per line,
# each tagged with its printed page:
#
#   @<page>\t<text>
#
# "@part\t<label>" where a part begins, the notes as "@note\t[^n]: …"
# (numbered through the book, as the transcription numbers them; build.py
# numbers them from 1 in each part). A line set centred is <Center>…</Center>,
# one set to the right <Right>…</Right>, a short rule "---"; a table is
# "{{table N}}" (the transcription's Nth, in order), set by hand from the page
# in build.py. Italic is kept as *…*. A paragraph the transcription breaks at
# a page is joined where the print runs it on (its next page's first line not
# set in: source/indents.json, from the scan). sacred-texts corrected two of
# the print's misprints (its errata page): they are restored as printed.
#
#   python3 extract.py > oracles.txt

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "source" / "sacred-texts"
FILES = ["coz01.htm", "coz02.htm", "coz03.htm", "coz04.htm", "coz05.htm", "coz06.htm", "coz07.htm", "coz08.htm"]
LABELS = ["Preface", "Introduction", "The Oracles of Zoroaster", "Ideas", "Particular Souls", "Matter", "Magical and Philosophical Precepts", "Oracles from Porphyry"]
# The print's misprints, as sacred-texts' errata page gives them, by its
# number for each (pages 24, 34): the word as printed.
ERRATA = {"0": "Iuscrutable", "1": "668"}
# Each page's first line: set in (a paragraph begins) or not (runs on).
INDENTS = json.loads((HERE / "source" / "indents.json").read_text())


def md(fragment):
    s = re.sub(r'<A NAME="fr_(\d+)"></A><A HREF="#fn_\d+">.*?</A>', r"[^\1]", fragment, flags=re.I | re.S)
    s = re.sub(r'<A HREF="errata\.htm#(\d+)">(.*?)</A>', lambda m: ERRATA[m.group(1)], s, flags=re.I | re.S)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    # a space inside an italic's tags is outside it (Markdown closes no
    # italic after a space)
    s = re.sub(r"(<i>)((?:\s|&nbsp;)+)", r"\2\1", s, flags=re.I)
    s = re.sub(r"((?:\s|&nbsp;)+)(</i>)", r"\2\1", s, flags=re.I)
    s = re.sub(r"</?i>", "*", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s*\[paragraph continues\]\s*", " ", s)  # sacred-texts' mark at a page
    s = html.unescape(s).replace("\xa0", " ")
    s = "\n".join(" ".join(l.split()) for l in s.split("\n")).strip()
    s = re.sub(r"\*(\s*)\*", r"\1", s)  # adjacent italics
    s = s.replace("--", "—")
    return re.sub(r" \[\^", "[^", s)


BLOCK = re.compile(r"<table.*?</table>|<p[^>]*>.*?</p>|<h(\d)[^>]*>.*?</h\1>", re.S | re.I)

out, notes, tables = [], [], 0
for f, label in zip(FILES, LABELS):
    src = (SRC / f).read_text(encoding="utf-8")
    src = re.sub(r"(?s)<script.*?</script>", "", src)
    body = src[re.search(r"<h\d|<p><A NAME=\"page_", src, re.I).start() :]
    body = body[: body.index("<nav")]
    out.append(["part", label])
    # the part's first printed page (some heads come before its mark)
    page = {"coz01.htm": "3", "coz02.htm": "7", "coz03.htm": "23", "coz04.htm": "30", "coz05.htm": "36", "coz06.htm": "40", "coz07.htm": "46", "coz08.htm": "54"}[f]
    turned = False
    for m in BLOCK.finditer(body):
        b = m.group(0)
        if b.lower().startswith("<table"):
            tables += 1
            out.append([page, f"{{{{table {tables}}}}}"])
            continue
        if b.lower().startswith("<h"):
            if md(b) == "Footnotes":
                continue
            out.append([page, f"<H>{md(b)}"])  # a heading: build.py decides
            continue
        pm = re.search(r'name="page_([^"]+)"', b, re.I)
        after = None
        if pm:
            rest = re.sub(r'(?is)<A NAME="page_[^"]+">.*?</A>', "", b)
            if not md(rest):
                page = pm.group(1)
                turned = True
                continue
            # a page turns inside it (oracle 18's lines): it is the page's
            # it begins on, and the next is on the new one
            b, after = rest, pm.group(1)
        note = re.match(r'<p[^>]*>\s*<A NAME="fn_(\d+)"></A><A HREF="[^"]*#fr_\d+">[^<]*</A>\s*(.*)', b, flags=re.S | re.I)
        if note:
            notes.append(f"[^{note.group(1)}]: {md(note.group(2)).strip()}")
            continue
        if re.match(r'<p[^>]*>\s*<A HREF="coz', b) or "Next:" in b:
            continue
        align = re.match(r'<p\s+align="(\w+)"', b, re.I)
        align = align.group(1).lower() if align else None
        text = md(b)
        if not text:
            continue
        was_turned, turned = turned, False
        if align == "center":
            text = "---" if set(text) <= set("_\n ") else f"<Center>{text}</Center>"
        elif align == "right":
            text = f"<Right>{text}</Right>"
        last = out[-1]
        if was_turned and align is None and last[0] != "part" and not last[1].startswith(("<", "{", "---")) and INDENTS.get(page) is False:
            last[1] += ("" if last[1].endswith("—") or text.startswith("—") else " ") + text
        else:
            out.append([page, text])
        if after:
            page = after

for page, text in out:
    print(f"@part\t{text}" if page == "part" else f"@{page}\t{text.replace(chr(10), chr(92) + 'n')}")
for n in notes:
    print(f"@note\t{n}")
