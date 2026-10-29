# The Cloud upon the Sanctuary, Isabel de Steiger's translation, third
# issue, revised and enlarged, with A. E. Waite's introduction (London:
# William Rider & Son, [1909]), from the sacred-texts.com transcription of
# it (source/sacred-texts/cuts02.htm … cuts08.htm, saved by the Wayback
# Machine), as Markdown paragraphs, one per line, each tagged with its page
# (the print's page number):
#
#   @<page>\t<text>
#
# "@part\t<label>" where a part begins (the Introduction, each Letter), and
# the notes as "@note\t[^n]: …". Italic is kept as *…*; a paragraph the
# transcription breaks at a page is joined. The book's title over Letter I
# and the parts' heads are the record's and the parts' names. sacred-texts
# corrected three of the print's misprints (its errata page, errata.htm);
# they are restored as printed.
#
#   python3 extract.py > cloud.txt

import html
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "source" / "sacred-texts"
FILES = ["cuts02.htm", "cuts03.htm", "cuts04.htm", "cuts05.htm", "cuts06.htm", "cuts07.htm", "cuts08.htm"]
LABELS = ["Introduction", "Letter I", "Letter II", "Letter III", "Letter IV", "Letter V", "Letter VI and Last"]
# The print's misprints, as sacred-texts' errata page gives them, by its
# number for each (pages xii, 43, 58): the word as printed.
ERRATA = {"0": "manuels", "1": "ignorauce", "2": "glorfied"}


def md(fragment):
    s = re.sub(r'<A NAME="fr_(\d+)"></A><A HREF="#fn_\d+"><FONT SIZE="1">\*</FONT></A>', r"[^\1]", fragment, flags=re.I)
    s = re.sub(r'<A NAME="fr_(\d+)"></A><A HREF="#fn_\d+">.*?</A>', r"[^\1]", s, flags=re.I | re.S)
    s = re.sub(r'<span class="contnote">.*?</span>', "", s, flags=re.S | re.I)
    # sacred-texts' corrections, each a link to its errata: the print's word.
    s = re.sub(r'<A HREF="errata\.htm#(\d+)">(.*?)</A>', lambda m: ERRATA[m.group(1)], s, flags=re.I | re.S)
    s = re.sub(r'<span style="font-variant:small-caps;">(.*?)</span>', r"\1", s, flags=re.S)
    s = re.sub(r"</?i>", "*", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = " ".join(s.split())
    s = re.sub(r"\*(\s*)\*", r"\1", s)  # adjacent italics
    return re.sub(r" \[\^", "[^", s)


out, notes = [], []
for f, label in zip(FILES, LABELS):
    src = (SRC / f).read_text(encoding="utf-8")
    body = src[src.index('name="page_') - 40 :]  # from the first page
    body = body[: body.index("Next:")] if "Next:" in body else body
    out.append(["part", label, False])
    page = None
    turned = False
    for b in re.findall(r"<p[^>]*>(.*?)</p>|<h[13][^>]*>(.*?)</h[13]>", body, flags=re.S | re.I):
        para, head = b
        if head:
            continue  # the book's title, the part's head
        m = re.search(r'name="page_([^"]+)"', para)
        if m:
            page = m.group(1)
            turned = True
            continue
        note = re.match(r'\s*<A NAME="fn_(\d+)"></A>.*?<A HREF="[^"]*#fr_\d+">[^<]*</A>\s*(.*)', para, flags=re.S | re.I)
        if note:
            notes.append(f"[^{note.group(1)}]: {md(note.group(2)).lstrip('* ').strip()}")
            continue
        text = md(para)
        if not text or text.startswith("Next:"):
            continue
        cont = "contnote" in para
        was_turned, turned = turned, False
        last = out[-1]
        if was_turned and last[0] != "part" and (cont or not re.search(r"[.?!:;\"')*”’]$", last[1]) or text[:1].islower()):
            last[1] += ("" if last[1].endswith("—") or text.startswith("—") else " ") + text
        else:
            out.append([page, text, False])

lines = []
for page, text, _ in out:
    lines.append(f"@part\t{text}" if page == "part" else f"@{page}\t{text}")
text = "\n".join(lines)
print(text)
for n in notes:
    print(f"@note\t{n}")
