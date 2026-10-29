# Builds the site's text of The Chaldæan Oracles of Zoroaster (Collectanea
# Hermetica, Volume VI; London: Theosophical Publishing Society, 1895), from
# the sacred-texts.com transcription of it:
#
#   extract.py   the transcription's blocks, by printed page (oracles.txt)
#   edits.json   every change made to them, each with its reason ("typing":
#                the transcription's slips, read on the 1895 scan,
#                source/scan.pdf; "as printed": the print's own, restored)
#   compare.py   the text against two readings of the scan, word by word;
#   punct.py     and mark by mark (run on oracles-edited.txt, which this
#                writes)
#   look.py      crops of the scan, to read a place on the page
#
#   python3 build.py
#
# writes ../chaldean-oracles/01.mdx, 02.mdx …, the
# parts books.json names: the Preface, the Introduction, then the Oracles'
# six sections. Every edit must match once (or "count" times), or the build
# stops. The Introduction's schemes (pp. 9–11), which the transcription has
# as layout tables, are set here from the page (SCHEMES); a part's heads are
# its name in books.json, its subtitle a centred line; the print's short
# rules are <Rule />, the double rule closing the schemes "---"; notes are
# numbered from 1 in each part.

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parent
edits = json.loads((HERE / "edits.json").read_text())

lines = subprocess.run([sys.executable, "-I", str(HERE / "extract.py")], capture_output=True, text=True, check=True).stdout
(HERE / "oracles.txt").write_text(lines)

failed = []
for e in edits:
    n = lines.count(e["find"])
    if n != e.get("count", 1):
        failed.append(f'{n}x (wants {e.get("count", 1)}): {e["find"][:70]!r}')
        continue
    lines = lines.replace(e["find"], e["replace"])
if failed:
    sys.exit("edits that do not match as they say:\n  " + "\n  ".join(failed))
(HERE / "oracles-edited.txt").write_text(lines)

# The schemes, read on the page (pp. 9–11): a row a band between the
# print's rules (a short rule within a column, a row too); a cell's lines as
# printed.
SCHEMES = {
    1: """\
| The Intelligibles<br />World of Supra-mundane Light | The Paternal Depth<br />The First Mind |
| :---: | :---: |
| | The Intelligible Triad<br />Pater: Mater or Potentia: Mens |
| | The Second Mind |
| Intelligibles and Intellectuals<br />in the<br />Empyræan World | Iynges<br />Synoches<br />Teletarchæ |
| Intellectuals<br />in the<br />Ethereal World | (The Third Mind.)<br />Three Cosmagogi<br />(Intellectual guides inflexible.)<br />Three Amilicti<br />(Implacable thunders). |
| Elementary World<br />The Demiurgos of the<br />Material Universe | Hypezokos<br />(Flower of Fire)<br />Effable, Essential and<br />Elemental Orders |
| | The Earth-Matter |""",
    2: """\
| World of Atziluth<br />or of God | The Boundless<br />The Illimitable<br />Light | Ain Suph.<br />Ain Suph Aur<br /><br />A radiant triangle. |
| :---: | :---: | :---: |
| World of Briah<br />Divine Forces | Kether<br />(crown)<br />Binah<br />(Intelligence) | <br /><br />Chokmah<br />(Wisdom) |
| World of Yetzirah<br />or of Formation | Geburah<br />Tiphereth<br />Hod<br />Yesod | Chesed<br /><br />Netzach |
| World of Assiah<br /><br />Material Form. | Malkuth<br />Ruled by<br />Adonai Melekh | |
| | The Earth-Matter. | |""",
    3: "<Center>I. Hyperarchii—Archangels<br />\nII. Azonœi—Unzoned gods<br />\nIII. Zonœi—Planetary Deities.</Center>",
    4: "<Center>Fiery<br />\nAiry<br />\nEarthy<br />\nWatery</Center>\n\n<Rule />\n\n<Center>Evil demons<br />\nLucifugous; the kliphoth</Center>",
    5: "<Center>Father. Mind. Fire.<br />\nMonad. Dyad. Triad.</Center>\n\n<Rule />",  # the rule under it, which the transcription lacks (p. 23)
}
# A part's heads (its name in books.json) and the title over the Preface
# are left out; its byline and subtitle are centred lines, the small
# capitals as the print's capitals show them.
HEADS = {
    "THE CHALDÆAN ORACLES": None, "ATTRIBUTED TO": None, "ZOROASTER.": None, "PREFACE": None,
    "By SAPERE AUDE.": "<Center>By Sapere Aude.</Center>",
    "INTRODUCTION": None,
    "By L. O.": "<Center>By L. O.</Center>",
    "CHALDÆAN SCHEME.": "### Chaldæan Scheme",
    "KABALISTIC SCHEME.": "### Kabalistic Scheme",
    "CHALDÆAN SCHEME OF BEINGS.": "### Chaldæan Scheme of Beings",
    "THE": None, "ORACLES OF ZOROASTER.": None,
    "IDEAS.": None,
    "INTELLIGIBLES, INTELLECTUALS, IYNGES, SYNOCHES, TELETARCHÆ, FOUNTAINS, PRINCIPLES, HECATE AND DÆMONS.": "<Center>Intelligibles, Intellectuals, Iynges, Synoches, Teletarchæ, Fountains, Principles, Hecate and Dæmons.</Center>",
    "PARTICULAR SOULS.": None,
    "SOUL, LIFE, MAN.": "<Center>Soul, Life, Man.</Center>",
    "MATTER.": None,
    "THE WORLD—AND NATURE.": "<Center>The World—and Nature.</Center>",
    "MAGICAL AND PHILOSOPHICAL PRECEPTS": None,
    "ORACLES FROM PORPHYRY.": None,
}
CENTRED = {"<Center>CAUSE. GOD.</Center>": "<Center>Cause. God.</Center>"}

def quotes(s):
    """The print's space inside quotation marks (" A solar world … subsist! ")
    is its setting, not the text's: closed up, in a block whose marks pair up
    (the first opens, the next closes); one that does not is left as it is."""
    if s.count('"') % 2:
        return s
    out, opening = "", True
    for part in re.split(r'(")', s):
        if part == '"':
            out = out if opening else out.rstrip(" ")
            out += '"'
            opening = not opening
        else:
            out += part.lstrip(" ") if not opening and out.endswith('"') else part
    return out


parts, notes = [], {}  # [label, blocks]; notes by the transcription's number
for line in lines.splitlines():
    tag, text = line.split("\t", 1)
    if tag == "@part":
        parts.append([text, []])
        continue
    if tag == "@note":
        m = re.match(r"\[\^(\d+)\]: (.*)", text)
        notes[m.group(1)] = m.group(2)
        continue
    if text.startswith("<H>"):
        h = text[3:]
        if h not in HEADS:
            sys.exit(f"a head not provided for: {h!r}")
        if HEADS[h]:
            parts[-1][1].append(HEADS[h])
        continue
    m = re.fullmatch(r"\{\{table (\d+)\}\}", text)
    if m:
        parts[-1][1].append(SCHEMES[int(m.group(1))])
        continue
    text = CENTRED.get(text, text)
    text = quotes(text)
    if text == "---":
        # the double rule closing the schemes (p. 11) is a break; the rest
        # are short rules
        text = "---" if tag == "@11" and parts[-1][1][-1].startswith("<Center>Fiery") else "<Rule />"
        # the rule under the Oracles' title (p. 23), now the part's name
        if not parts[-1][1]:
            continue
    # a line the print breaks (oracle 18's verse)
    text = text.replace("\\n", "<br />\n")
    # a numbered oracle or list item is the print's text, not a Markdown list
    text = re.sub(r"^(\d+)\. ", r"\1\\. ", text)
    parts[-1][1].append(text)

labels = ["Preface", "Introduction", "The Oracles of Zoroaster", "Ideas", "Particular Souls", "Matter", "Magical and Philosophical Precepts", "Oracles from Porphyry"]
if [p[0] for p in parts] != labels:
    sys.exit(f"parts: {[p[0] for p in parts]}")

SITE.mkdir(parents=True, exist_ok=True)
for old in SITE.glob("[0-9][0-9].mdx"):
    old.unlink()
words, used = 0, set()
for i, (label, blocks) in enumerate(parts, 1):
    text = "\n\n".join(blocks) + "\n"
    # notes: numbered from 1 in the part, in the order their marks come
    order = []
    for n in re.findall(r"\[\^(\d+)\]", text):
        if n not in order:
            order.append(n)
    for k, n in enumerate(order, 1):
        text = text.replace(f"[^{n}]", f"[^@{k}]")
        used.add(n)
    text = text.replace("[^@", "[^")
    if order:
        text += "\n" + "\n".join(f"[^{k}]: {notes[n]}" for k, n in enumerate(order, 1)) + "\n"
    bare = re.sub(r"</?(Center|Right)>|<Rule />|<br />", "", text)
    if re.search(r"[{}<>]", bare):
        sys.exit(f"{label}: text has {{ }} < or > that MDX would read as code: {re.search(r'.{30}[{}<>].{30}', bare, re.S).group()!r}")
    (SITE / f"{i:02d}.mdx").write_text(text)
    words += len(bare.split())
if set(notes) - used:
    sys.exit(f"notes without a mark: {sorted(set(notes) - used)}")
print(f"{SITE}: {len(parts)} parts, {words} words")
