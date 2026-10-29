#!/usr/bin/env python3
"""How the School of Ageless Wisdom's lessons came into this repository
(October 2026): from the agelesswisdom site's own tree, where they had
been transcribed and corrected since 2025, into the format here. Kept as
provenance; it was run once.

    python3 port.py /path/to/agelesswisdom

For each of the seven sections (a part each), in curriculum order:
  - content/lessons/en/<section>/NN-<id>.mdx  ->  <section>/NN.mdx,
    the headings set one level down (the site's `# Title` is the format's
    `## Title`: the text's own top heading), the links between lessons
    made relative to this edition (`../section-a/09.mdx#p12`,
    `03.mdx`, `../section-b/` for a section), the figures referenced
    from the edition's images/ (`../images/<section>/img-13.jpeg`);
  - public/images/lessons/<section>/*  ->  images/<section>/.
Nothing in the words is changed.
"""

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDITION = HERE.parent
SRC = Path(sys.argv[1]).resolve()

SECTIONS = [
    "section-a",
    "section-b",
    "section-c",
    "section-d",
    "section-first",
    "section-second",
    "hermetic-alchemy",
]

curriculum = {
    s["id"]: s for s in json.loads((SRC / "content/curriculum/en.json").read_text())
}
# Every lesson's number in its section, by "<section>/<id>".
number = {}
for sec in SECTIONS:
    for i, lesson in enumerate(curriculum[sec]["lessons"], 1):
        number[f"{sec}/{lesson['id']}"] = i


def relink(text: str, section: str, where: str) -> str:
    def lesson_link(m):
        target, fragment = m.group(1), m.group(2) or ""
        if target not in number:
            raise SystemExit(f"{where}: link to {target}, which is not a lesson here")
        sec, _ = target.split("/")
        n = number[target]
        rel = f"{n:02d}.mdx" if sec == section else f"../{sec}/{n:02d}.mdx"
        return f"]({rel}{fragment})"

    text = re.sub(r"\]\(/([a-z-]+/[a-z0-9-]+)(#p\d+)?\)", lesson_link, text)

    def section_link(m):
        sec = m.group(1)
        if sec not in SECTIONS:
            raise SystemExit(f"{where}: link to section {sec}, which is not here")
        return f"](../{sec}/)"

    text = re.sub(r"\]\(/#([a-z-]+)\)", section_link, text)
    return text


def refigure(text: str, section: str, where: str) -> str:
    def figure(m):
        sec, name = m.group(1), m.group(2)
        if sec != section:
            raise SystemExit(f"{where}: figure from another section, {sec}/{name}")
        return f"](../images/{sec}/{name})"

    return re.sub(r"\]\(/images/lessons/([a-z-]+)/([^)\s]+)\)", figure, text)


def reheading(text: str) -> str:
    # One level down, outside code: the lessons have no code blocks.
    return re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", text, flags=re.M)


copied = 0
for sec in SECTIONS:
    out = EDITION / sec
    out.mkdir(exist_ok=True)
    files = sorted((SRC / "content/lessons/en" / sec).glob("*.mdx"))
    if len(files) != len(curriculum[sec]["lessons"]):
        raise SystemExit(f"{sec}: {len(files)} files, {len(curriculum[sec]['lessons'])} lessons")
    for i, (f, lesson) in enumerate(zip(files, curriculum[sec]["lessons"]), 1):
        if not f.name.startswith(f"{i:02d}-{lesson['id']}."):
            raise SystemExit(f"{sec}: {f.name} is not lesson {i}, {lesson['id']}")
        text = f.read_text()
        where = f"{sec}/{f.name}"
        text = reheading(refigure(relink(text, sec, where), sec, where))
        (out / f"{i:02d}.mdx").write_text(text)
        copied += 1
    images = SRC / "public/images/lessons" / sec
    if images.exists():
        dest = EDITION / "images" / sec
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(images, dest)

print(f"{copied} lessons into {EDITION}")
