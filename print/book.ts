/**
 * A book: one edition set as a PDF. A title page (from book.json), then
 * the text: one file, or its contents a file each, every one opening on a
 * fresh page under its label ("Chapter I", "Letter II", "Lesson 1"), and
 * where the contents are gathered in parts (the README), each part opening
 * on a page of its own under its title, its contents one level down. US
 * Letter, the lessons' page and type, so a book and a lesson from the same
 * shelf look alike. The text's own headings (## in the source) are the
 * chapter headings; the renderer sets them one level under the entry's
 * label, and a part's entries one further. The editors' note on the text
 * and a colophon (book.json's `publicDomain` and `note`, the revision set
 * from) are not printed for now: the notes are being rewritten.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import {
  FONT_STACK,
  type Renderer,
  escapeHtml,
  fontFaceCss,
  sharedElementsCss,
} from "./render.ts";

/** A book's contents, a file each (01.mdx …): how many ("Lesson N" each),
 *  or what each is called. */
export type Contents = number | string[];

/** A part of a book in parts: its contents in a folder of its own. */
export interface PartRecord {
  title: string;
  /** The folder, under the edition's, holding its 01.mdx … */
  dir: string;
  contents: Contents;
}

/** An edition's record, book.json (the README). */
export interface BookRecord {
  title: string;
  subtitle?: string;
  author: string;
  imprint: string;
  short: string;
  edition: string;
  translator?: string;
  editor?: string;
  /** The year of the printing held, where it is known. */
  year?: number;
  /** The language of this edition's text ("English"); the work's if absent. */
  language?: string;
  publicDomain: string;
  note: string;
  /** The text's contents, a file each (01.mdx … in the folder); neither
   *  this nor `parts`, one text (text.mdx). */
  contents?: Contents;
  /** A book in parts, each a folder with contents of its own. */
  parts?: PartRecord[];
}

/** One of the contents to set: its file, and its label where the book has
 *  contents. */
export interface Entry {
  file: string;
  label?: string;
}

/** A part of the book as set: the entries it gathers, under its title
 *  where it has one (an ungathered book is one part without). */
export interface Part {
  title?: string;
  /** Its folder's name, where the book is in parts. */
  dir?: string;
  entries: Entry[];
}

export interface BookSource {
  /** The folder holding the works. */
  root: string;
  work: string;
  edition: string;
}

/** What each of the contents is called: as named, or "Lesson N". */
export function contentsLabels(contents: Contents): string[] {
  return typeof contents === "number"
    ? Array.from({ length: contents }, (_, i) => `Lesson ${i + 1}`)
    : contents;
}

/** The file of the Nth of the contents, 01.mdx … */
export const entryFile = (n: number) => `${String(n).padStart(2, "0")}.mdx`;

/** The contents of a folder, 01.mdx … NN.mdx, checked: each present, and
 *  none beyond N. */
function entriesOf(dir: string, contents: Contents, where: string): Entry[] {
  const labels = contentsLabels(contents);
  const entries = labels.map((label, i) => ({
    file: path.join(dir, entryFile(i + 1)),
    label,
  }));
  for (const { file } of entries) {
    if (!fs.existsSync(file)) throw new Error(`${where}: no ${file}`);
  }
  const present = fs
    .readdirSync(dir)
    .filter((f) => /^\d{2}\.mdx$/.test(f)).length;
  if (present !== entries.length) {
    throw new Error(
      `${where}: book.json names ${entries.length} contents; ${dir} has ${present}`,
    );
  }
  return entries;
}

/** The edition's record and its text, part by part, in order. */
export function readBook({ root, work, edition }: BookSource) {
  const dir = path.join(root, work, edition);
  const where = `${work}/${edition}`;
  const record = JSON.parse(
    fs.readFileSync(path.join(dir, "book.json"), "utf8"),
  ) as BookRecord;
  if (record.contents && record.parts) {
    throw new Error(`${where}: book.json gives both contents and parts`);
  }
  let parts: Part[];
  if (record.parts) {
    parts = record.parts.map((part) => ({
      title: part.title,
      dir: part.dir,
      entries: entriesOf(path.join(dir, part.dir), part.contents, where),
    }));
  } else if (record.contents) {
    parts = [{ entries: entriesOf(dir, record.contents, where) }];
  } else {
    const file = path.join(dir, "text.mdx");
    if (!fs.existsSync(file)) throw new Error(`${where}: no ${file}`);
    parts = [{ entries: [{ file }] }];
  }
  return { dir, record, parts };
}

/** The HTML lang of an edition's language, for hyphenation and the viewer. */
export function langOf(language: string | undefined): string {
  const codes: Record<string, string> = {
    English: "en",
    German: "de",
    French: "fr",
    Spanish: "es",
    Italian: "it",
    Latin: "la",
    Greek: "el",
    Hebrew: "he",
  };
  return codes[language ?? "English"] ?? "en";
}

export function bookCss(record: BookRecord): string {
  const foot = escapeCss(record.short);
  return `${fontFaceCss()}
@page {
  size: 8.5in 11in;
  margin: 1in 1.4in 0.85in;
  @bottom-center {
    content: counter(page);
    font-family: ${FONT_STACK};
    font-size: 9pt;
    color: #6b6456;
  }
  @bottom-right {
    content: "${foot}";
    font-family: ${FONT_STACK};
    font-size: 8pt;
    letter-spacing: 0.02em;
    color: #9a927f;
  }
}
/* The title page carries no running foot. */
@page :first {
  @bottom-center { content: none; }
  @bottom-right { content: none; }
}
* {
  box-sizing: border-box;
}
html {
  color: #211f1a;
  font-family: ${FONT_STACK};
  font-size: 11.5pt;
  line-height: 1.5;
}
/* See lessons.ts in botaschool on the 1px: a Chrome print rounding bug. */
body {
  margin: 0;
  padding-right: 1px;
  font-kerning: normal;
  text-rendering: optimizeLegibility;
}
h1, h2, h3, h4, p {
  margin: 0;
}
/* The title page: the title a third of the way down, the rest beneath. */
.title-page {
  break-after: page;
  padding-top: 2.6in;
  text-align: center;
}
/* pre-wrap on the headings: Chrome's outline takes a heading's text as laid
   out and drops the space at every soft wrap ("InvisibleRosicrucian") unless
   the spaces are preserved. */
.title-page h1,
.part-masthead h2,
.book-body h3,
.book-body h4,
.book-body h5 {
  white-space: pre-wrap;
}
.title-page h1 {
  font-size: 24pt;
  font-weight: 700;
  line-height: 1.2;
}
.title-page .subtitle {
  font-size: 12.5pt;
  font-style: italic;
  line-height: 1.4;
  margin: 0.22in auto 0;
  max-width: 4.4in;
}
.title-page .author {
  font-size: 12pt;
  letter-spacing: 0.12em;
  margin-top: 0.7in;
  text-transform: uppercase;
}
.title-page .imprint {
  color: #6b6456;
  font-size: 10pt;
  line-height: 1.45;
  margin: 1.2in auto 0;
  max-width: 4.4in;
}
/* Each entry of the contents on a fresh page, its label over it as the
   lessons' eyebrow; in a book in parts, the part's title above the label. */
.part {
  break-before: page;
}
.part-masthead {
  margin-bottom: 0.34in;
}
.part-masthead h2,
.part-masthead h3 {
  color: #6b6456;
  font-size: 10.5pt;
  font-variant-caps: all-small-caps;
  font-weight: 400;
  letter-spacing: 0.14em;
}
.part-masthead .eyebrow {
  color: #9a927f;
  font-size: 9pt;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  margin-bottom: 0.04in;
}
.part-masthead .rule {
  border: 0;
  border-top: 0.75pt solid #cbc4b4;
  margin: 0.14in 0 0;
}
/* A part's own page: its title alone, a third of the way down. */
.part-page {
  break-before: page;
  padding-top: 3.4in;
  text-align: center;
}
.part-page h2 {
  font-size: 18pt;
  font-variant-caps: all-small-caps;
  font-weight: 650;
  letter-spacing: 0.08em;
  line-height: 1.2;
  white-space: pre-wrap;
}
/* The text's headings: ## is the chapter's (set as the lessons set theirs),
   ### the section's; within a part each sits one level further down. */
.book-body h3,
.book-body h4,
.book-body h5,
.book-body h6 {
  break-after: avoid;
  font-weight: 650;
  line-height: 1.2;
  margin: 0.26in 0 0.08in;
  text-align: center;
}
.book-body h3,
.nested .book-body h4 {
  font-size: 16pt;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.04em;
}
.book-body h4,
.nested .book-body h5 {
  font-size: 12.5pt;
}
.book-body p {
  hyphens: auto;
  orphans: 3;
  text-align: justify;
  widows: 3;
}
/* The classic book setting: paragraphs run on, the first line indented. */
.book-body p + p {
  text-indent: 0.3in;
}
.book-body h3 + p,
.book-body h4 + p,
.book-body h5 + p,
.book-body h6 + p,
.book-body blockquote + p,
.book-body figure + p,
.book-body table + p,
.book-body ol + p,
.book-body ul + p {
  text-indent: 0;
}
.book-body p.centered,
.book-body p.right-set,
.book-body p.editor-note {
  text-indent: 0;
}
${sharedElementsCss()}`;
}

function escapeCss(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

export interface BookDocumentOptions extends BookSource {
  renderer: Renderer;
  /** The repository's revision the text is set from (git describe), and
   *  the day: for the colophon, when it is printed again. */
  revision: string;
  date: string;
}

/** A part's entries set one level down: the renderer's h3 (## in the
 *  source) becomes h4, and so on; the part's title is the h2 and the
 *  entry's label the h3, so the outline nests part, entry, heading. */
const nest = (body: string) =>
  body.replace(
    /<(\/?)h([3-5])\b/g,
    (_, slash: string, level: string) => `<${slash}h${Number(level) + 1}`,
  );

/** The whole document, as HTML for Chrome. */
export function bookDocumentHtml(options: BookDocumentOptions): string {
  const { record, parts } = readBook(options);
  const { renderer } = options;
  // The anchors a link within the text points at (remark-book-links, given
  // "#{part}-{n}" and "#{part}" by build.ts).
  const sections = parts.flatMap((part) => {
    const out: string[] = [];
    if (part.title) {
      out.push(`<section class="part-page" id="${escapeHtml(part.dir ?? "")}">
    <h2>${escapeHtml(part.title)}</h2>
  </section>`);
    }
    part.entries.forEach(({ file, label }, i) => {
      const markdown = fs.readFileSync(file, "utf8");
      const body = renderer.mdxToHtml(markdown, file);
      const id = part.dir ? `${part.dir}-${i + 1}` : `entry-${i + 1}`;
      if (part.title) {
        out.push(`<section class="part nested" id="${escapeHtml(id)}">
    <header class="part-masthead">
      <div class="eyebrow">${escapeHtml(part.title)}</div>
      <h3>${escapeHtml(label ?? "")}</h3>
      <hr class="rule">
    </header>
    <div class="book-body">
${nest(body)}
    </div>
  </section>`);
      } else {
        const masthead = label
          ? `<header class="part-masthead">
      <h2>${escapeHtml(label)}</h2>
      <hr class="rule">
    </header>`
          : "";
        out.push(`<section class="part"${label ? ` id="${escapeHtml(id)}"` : ""}>
    ${masthead}
    <div class="book-body">
${body}
    </div>
  </section>`);
      }
    });
    return out;
  });
  const people = [
    record.translator && `Translated by ${record.translator}`,
    record.editor && `Edited by ${record.editor}`,
  ].filter(Boolean) as string[];
  return `<!doctype html>
<html lang="${langOf(record.language)}">
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(record.title)}</title>
  <style>${bookCss(record)}</style>
</head>
<body>
  <section class="title-page">
    <h1>${escapeHtml(record.title)}</h1>
    ${record.subtitle ? `<p class="subtitle">${escapeHtml(record.subtitle)}</p>` : ""}
    <p class="author">${escapeHtml(record.author)}</p>
    <p class="imprint">${escapeHtml(record.imprint)}${people.length ? `<br>${people.map(escapeHtml).join("<br>")}` : ""}</p>
  </section>
${sections.join("\n")}
</body>
</html>`;
}
