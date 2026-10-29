# Books

Public-domain books of the Western esoteric tradition.

| Work | Edition | Which |
| --- | --- | --- |
| `fama-fraternitatis` | `1887-vaughan-waite` | Vaughan's translation (1652) as A. E. Waite printed it, *The Real History of the Rosicrucians*, 1887 |
| `confessio-fraternitatis` | `1887-vaughan-waite` | Vaughan's translation, revised by Waite against the Latin, 1887 |
| `true-and-invisible-rosicrucian-order` | `1927` | Paul Foster Case's first edition (the later, enlarged editions are in copyright) |
| `kybalion` | `1908` | The Yogi Publication Society, 1908, the first printing |
| `cloud-upon-the-sanctuary` | `1909-de-steiger` | Isabel de Steiger's translation, third issue, Rider, 1909, with Waite's introduction |
| `sepher-yetzirah` | `1923-stenring` | Knut Stenring's translation, Rider, 1923, with Waite's introduction (Stenring's Notes still to come) |
| `chaldean-oracles` | `1895-westcott` | W. Wynn Westcott's, Collectanea Hermetica VI, 1895 |
| `school-of-ageless-wisdom` | `typescript` | Paul Foster Case's lessons for the School, 95 in seven parts, from the School's own typed lessons (undated) |
| `oracle-of-tarot` | `typescript` | Case's course in divination by the Tarot, ten lessons, from the School's typed lessons (undated) |
| `correlation-of-sound-and-colour` | `typescript` | Case's text on the tones and the colours, with its four diagrams, from the School's typescript (undated) |


## Formatting

Markdown (CommonMark with GFM footnotes), with a few tags for what
Markdown cannot say. A renderer needs only these:

| Mark | Meaning |
| --- | --- |
| `## `, `### ` | The print's headings, as printed (closing full stops kept) |
| `> ` | A passage the print sets in from both margins: a quotation |
| `> ` with `<br />` after each line | Quoted verse, a line each (set one block per line) |
| `[^1]` … `[^1]:` | The print's footnotes |
| `*…*` | Italics as printed |
| `<Center>…</Center>` | A line the print sets centred (a dedication, "Finis") |
| `<Right>…</Right>` | A line the print sets to the right (an oracle's authority) |
| `<Rule />` | A short rule set centred, not a full-width break |
| `<EditorNote>…</EditorNote>` | A paragraph in the editors' voice, not the book's |
| `<EditorGap>…</EditorGap>` | The same within a line: a sign or figure the copy lacks, marked where it stood |
| `![…](images/<name>.png)` | A figure, from the edition's `images/`, by a path relative to the file |
| `[…](03.mdx)`, `[…](../section-a/09.mdx#p12)`, `[…](../section-b/)` | A link within the text, to one of its contents or to a part, relative to the edition |
| `<Cite>…</Cite>` | The source of the quotation before it, set under it |
| `<KeepTogether>…</KeepTogether>` | Kept on one page in print (a short list, a table with its heading) |
| `<TarotGroups />` | The tableau of the 112 nine-Key groups (the Tarot Instruction), drawn from `print/tarot-groups.ts` |

Dashes: a text keeps the print's dashes as `—`; the school's renderer also
turns `--` into one, and straight quotes into curly ones (smartypants),
so a text may use either. Plain inline HTML passes (`<br />`, `<sup>`).
Nothing else is interpreted: no JSX, no imports, no front matter.

A figure's alt text may end in `|WxH`, its size as shown in the print.
A consumer serves each edition's `images/` wherever it likes and rewrites
the relative path (botaschool serves them at
`/images/books/<work>/<edition>/`); it shows each of a text's contents
wherever it likes and rewrites a link to one the same way (`links` in
`mdx.mjs`; the repository's own print makes them links within the PDF).
