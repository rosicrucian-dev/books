# Builds the site's text of The Book of Formation (Sepher Yetzirah), Knut
# Stenring's translation, with A. E. Waite's introduction (London: William
# Rider & Son, 1923), from the proofread text (proofread/), every line read
# against the page images of the Google Books scan (source/scan.pdf):
#
#   proofread/introduction.txt     pp. 5–16
#   proofread/translators-note.txt p. 17, then Table I (p. 19)
#   proofread/chapters.txt         Chapters I–VI, pp. 21–32
#   proofread/tables.md            Tables I–V (pp. 19, 33–35), Markdown
#   proofread/32-paths.txt         The 32 Paths of Wisdom, pp. 58–66
#   proofread/works-used.txt       p. 67
#   figures.py                     the wheel of the 231 gates, the tables'
#                                  symbols (../images/)
#
# The .txt files are a paragraph a line, "@<printed page>\t<text>" (a line
# with no tag continues the one before it, after a <br />), "@part\t<label>"
# where a part begins, and "@note\t[^n]: …" for Stenring's footnotes.
# "{{table I}}" and "{{figure <name>}}" stand where a table or figure goes.
#
#   python3 build.py
#
# writes ../sepher-yetzirah/01.mdx, 02.mdx …, a part
# each, as books.json's "parts" name them. Footnotes are numbered from 1 on
# each page. Stenring's Notes on the text (pp. 36–57) are not set yet.

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
P = HERE / "proofread"
SITE = HERE.parent
IMAGES = HERE.parent / "images"
LABELS = ["Introduction", "Translator's Note"] + [f"Chapter {r}" for r in "I II III IV V VI".split()] + ["Tables", "The 32 Paths of Wisdom", "List of Works Used"]
FIGURES = {
    # name: (alt, width, height as shown)
    "wheel": ("The two hundred and thirty-one gates", 1325, 1338),
    "mothers": ("A triangle with a cross within it", 40, 36),
    "doubles": ("A hexagram with a point within it", 36, 39),
}

# Tables: Table I alone, then II–V, split at the source's comments.
tables = re.split(r"^<!--.*?-->\n", (P / "tables.md").read_text(), flags=re.M)
TABLE_I, TABLES = tables[1].strip(), tables[2].strip()


def read(name, label=None):
    """A file's parts: [label, paragraphs, notes]."""
    parts = [[label, [], {}]] if label else []
    for line in (P / name).read_text().splitlines():
        if not line.strip():
            continue
        if not line.startswith("@"):
            parts[-1][1][-1] += "\n" + line
            continue
        tag, text = line.split("\t", 1)
        if tag == "@part":
            parts.append([text, [], {}])
        elif tag == "@note":
            m = re.fullmatch(r"\[\^(\d+)\]: (.*)", text)
            parts[-1][2][m.group(1)] = m.group(2)
        else:
            parts[-1][1].append(text)
    return parts


parts = (
    read("introduction.txt", "Introduction")
    + read("translators-note.txt", "Translator's Note")
    + read("chapters.txt")
    + [["Tables", ["{{tables}}"], {}]]
    + read("32-paths.txt", "The 32 Paths of Wisdom")
    + read("works-used.txt", "List of Works Used")
)
if [p[0] for p in parts] != LABELS:
    sys.exit(f"parts: {[p[0] for p in parts]}")


def figure(m, cell=False):
    name = m.group(1)
    if not (IMAGES / f"{name}.png").exists():
        sys.exit(f"no image {name}.png: run figures.py")
    alt, w, h = FIGURES[name]
    # In a table's cell the "|" before the size is escaped, or it ends the cell.
    bar = "\\|" if cell else "|"
    return f"![{alt}{bar}{w}x{h}](images/{name}.png)"


def para(t):
    t = t.replace("{{table I}}", TABLE_I).replace("{{tables}}", TABLES)
    t = "\n".join(re.sub(r"\{\{figure (\w+)\}\}", lambda m: figure(m, l.startswith("|")), l) for l in t.split("\n"))
    # A verse's number is the print's, not a list's.
    t = re.sub(r"^(\d+)\. ", r"\1\\. ", t)
    t = re.sub(r"^(\d+)\.$", r"\1\\.", t)
    return t


SITE.mkdir(parents=True, exist_ok=True)
for old in SITE.glob("[0-9][0-9].mdx"):
    old.unlink()
words = 0
for i, (label, paras, notes) in enumerate(parts, 1):
    text = "\n\n".join(para(p) for p in paras) + "\n"
    # This page's notes, numbered from 1.
    order = {old: str(k) for k, old in enumerate(dict.fromkeys(re.findall(r"\[\^(\d+)\]", text)), 1)}
    if set(order) != set(notes):
        sys.exit(f"{label}: notes {sorted(notes)}, referenced {sorted(order)}")
    text = re.sub(r"\[\^(\d+)\]", lambda m: f"[^{order[m.group(1)]}]", text)
    for old, new in order.items():
        text += f"\n[^{new}]: {notes[old]}\n"
    bare = re.sub(r"</?(Center|u)>|<br />|!\[[^\]]*\]\([^)]*\)", "", text)
    if re.search(r"[{}<>]", bare):
        sys.exit(f"{label}: text has {{ }} < or > that MDX would read as code: {re.search(r'.{0,40}[{}<>].{0,40}', bare).group()!r}")
    if re.search(r"⟦|⟧", text):
        sys.exit(f"{label}: a place still marked to be read")
    (SITE / f"{i:02d}.mdx").write_text(text)
    words += len(text.split())
print(f"{SITE}: {len(parts)} parts, {words} words")
