# The Fama and the Confessio as Waite printed them in The Real History of
# the Rosicrucians (London: George Redway, 1887), chapters III and IV, from
# the sacred-texts.com transcription (source/rhr06.htm, rhr07.htm), as
# Markdown paragraphs, one per line, each tagged with its page:
#
#   @<page>\t<text>
#
# Italic is kept as *…*; Waite's footnotes as [^n] with their text in
# lines "@note\t[^n]: …". Waite's own introduction to each chapter is left
# out; the Confessio's prefatory advertisement, which his introduction
# quotes, is kept, as the Confessio's own. A paragraph the transcription
# breaks at a page is joined; "[paragraph continues]" after an indented
# inscription starts a paragraph of its own.
#
#   python3 extract.py fama > fama.txt
#   python3 extract.py confessio > confessio.txt

import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
which = sys.argv[1]
src = (HERE / "source" / {"fama": "rhr06.htm", "confessio": "rhr07.htm"}[which]).read_text(encoding="utf-8")


def md(fragment):
    s = re.sub(r'<A NAME="fr_\d+"></A><A HREF="#fn_(\d+)"><FONT SIZE="1">\d+</FONT></A>', r"[^\1]", fragment)
    s = re.sub(r'<span class="contnote">.*?</span>', "", s, flags=re.S)
    s = re.sub(r"</?i>", "*", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = " ".join(s.split())
    s = re.sub(r"\*(\s*)\*", r"\1", s)  # adjacent italics
    return re.sub(r" \[\^", "[^", s)


blocks = re.findall(r"<p[^>]*>(.*?)</p>", src, flags=re.S | re.I)
page = None
out = []  # [page, text, joinable]
notes = []
started = False
turned = False  # a page marker since the last paragraph
for b in blocks:
    m = re.search(r'name="page_(\d+)"', b)
    if m:
        page = int(m.group(1))
        turned = True
        continue
    text = md(b)
    if not text:
        continue
    note = re.match(r'<A NAME="fn_(\d+)"></A><A HREF="[^"]+">\d+:\d+</A>\s*(.*)', b.strip(), flags=re.S)
    if note:
        if f"[^{note.group(1)}]" in "".join(t for _, t, _ in out):
            notes.append(f"[^{note.group(1)}]: {md(note.group(2))}")
        continue
    if text.startswith("Next:"):
        break
    if not started:
        if which == "fama" and text.startswith("*Fama Fraternitatis; or"):
            started = True  # the title is the book's record
        if which == "confessio" and text.startswith('"Here, gentle reader'):
            started = True
        else:
            continue
    if which == "confessio" and text.startswith("*Confessio Fraternitatis R. C. ad"):
        continue  # the title, the book's record
    if re.fullmatch(r"CHAPTER [IVXL]+\.", text):
        out.append([page, f"## Chapter {text.split()[1].rstrip('.')}", False])
        continue
    cont = "[paragraph continues]" in b
    indented = "margin-left" in b
    was_turned, turned = turned, False
    if was_turned and out and out[-1][2] and not cont and not indented and not text.startswith("##") and (
        not re.search(r"[.?!:;\"')*]$|--$", out[-1][1]) or text[:1].islower()
    ):
        out[-1][1] += " " + text
    else:
        out.append([page, text, not indented])

for p, t, _ in out:
    print(f"@{p}\t{t}")
for n in notes:
    print(f"@note\t{n}")
