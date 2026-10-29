# Builds the site's text of The True and Invisible Rosicrucian Order
# (1927) from the 2003 transcription (source.pdf):
#
#   paragraphs.txt  extract.py's paragraphs, page-tagged, italic/bold kept
#   edits.json      every change made to them, each with its reason:
#                   "structure" (lists, headings, the table, page joins),
#                   "typing" (the transcription's slips), "gap" (a figure
#                   the transcription does not have)
#
#   python3 books/true-and-invisible-rosicrucian-order/build.py
#
# writes ../true-and-invisible-rosicrucian-order/
# 01.mdx … 03.mdx, a page each (MDX: the site renders them with
# the lessons' pipeline, mdx.config.mjs). The book is three lessons: the
# second and third are headed "Lesson 2" and "Lesson 3", the first only by
# the book's own heading; the site calls it "Lesson 1" (ours, not Case's),
# and each lesson's name is its page's title, not a heading in its text.
# Every edit must match exactly once, or the build stops.

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent

paras = []
for line in (HERE / "paragraphs.txt").read_text().splitlines():
    page, text = line.split("\t", 1)
    paras.append((int(page[1:]), text))

# The title page (page 1) is the book's record (books.json), not its text.
body = [(p, t) for p, t in paras if p > 1]

text = "\n\n".join(t for _, t in body) + "\n"

edits = json.loads((HERE / "edits.json").read_text())
failed = []
for e in edits:
    n = text.count(e["find"])
    if n != 1:
        failed.append(f'{n}x: {e["find"][:70]!r}')
        continue
    text = text.replace(e["find"], e["replace"])
if failed:
    sys.exit("edits that do not match exactly once:\n  " + "\n  ".join(failed))

# The typescript's dashes: "--", which the site sets as a dash as it does
# the lessons' (remark-smartypants); a spaced hyphen is one too.
text = re.sub(r"(?<=\w) - ?(?=\w)", " -- ", text)

# Case's numbers are his text, not Markdown lists: a paragraph begins
# with its number as printed ("3\." keeps Markdown from renumbering it or
# setting it as a list item, its following paragraphs out of line).
text = re.sub(r"^(\d+)\. ", r"\1\\. ", text, flags=re.M)

# Nothing MDX would read as code.
if re.search(r"[{}]|<(?!/?Editor(Note|Gap)>)", text):
    sys.exit("text has { } or < that MDX would read as code")

lessons = re.split(r"^## Lesson [23]\n\n", text, flags=re.M)
if len(lessons) != 3:
    sys.exit(f"expected three lessons, found {len(lessons)}")

OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.mdx"):
    old.unlink()
for n, lesson in enumerate(lessons, 1):
    (OUT / f"{n:02d}.mdx").write_text(lesson.strip() + "\n")
print(f"{OUT}: {len(lessons)} lessons, {len(text.split())} words, {len(edits)} edits")
