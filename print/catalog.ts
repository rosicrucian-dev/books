/**
 * The catalog: what every edition is, as data, for the sites that list the
 * books (rosicrucian.dev's Books, a page per book). Written beside the PDFs
 * by build.ts (dist/catalog.json) and published with them, so a site reads
 * a book's edition, people and contents from here instead of keeping its
 * own copy that would drift from book.json.
 *
 * One entry per edition: its PDFs' names (print and screen, book.ts), the
 * record's descriptive fields as book.json gives them, and its contents,
 * part by part: each entry's label ("Chapter I", "Lesson 1") and its first
 * heading in the text, where it has one.
 */
import * as fs from "node:fs";
import { type BookRecord, PAGE_FORMATS, PUBLISHED, PUBLISHER, readBook } from "./book.ts";

export interface CatalogEntry {
  label?: string;
  heading?: string;
}

export interface CatalogPart {
  title?: string;
  entries: CatalogEntry[];
}

export interface CatalogBook {
  work: string;
  edition: string;
  /** Each edition's PDF, by page format: <name>.pdf, <name>-screen.pdf. */
  pdfs: Record<string, string>;
  title: string;
  subtitle?: string;
  author: string;
  translator?: string;
  editor?: string;
  imprint: string;
  /** book.json's `edition`: which printing or typing it is set from. */
  editionNote?: string;
  language: string;
  publisher: string;
  published: number;
  publicDomain: boolean;
  parts: CatalogPart[];
}

export interface Catalog {
  books: CatalogBook[];
}

/** Straight quotes curled, as the pipeline's smartypants curls them on
 *  the page: the catalog is shown as text, not run through the pipeline. */
function curl(text: string): string {
  return text.replace(/"([^"]*)"/g, "\u201c$1\u201d").replace(/'/g, "\u2019");
}
const curlMaybe = (text: string | undefined) => (text ? curl(text) : text);

/** The text of a heading's line, without the format's inline markup. */
function plain(markdown: string): string {
  return curl(
    markdown
      .replace(/<[^>]+>/g, "")
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/[*_`]/g, "")
      .replace(/\s+/g, " ")
      .trim(),
  );
}

/** An entry's first heading (## in the source), where it has one. */
function firstHeading(file: string): string | undefined {
  const match = /^##\s+(.+)$/m.exec(fs.readFileSync(file, "utf8"));
  return match ? plain(match[1]) || undefined : undefined;
}

export function catalogBook(
  root: string,
  work: string,
  edition: string,
  name: string,
): CatalogBook {
  const { record, parts } = readBook({ root, work, edition });
  const r: BookRecord = record;
  return {
    work,
    edition,
    pdfs: Object.fromEntries(
      PAGE_FORMATS.map((format) => [
        format,
        `${format === "print" ? name : `${name}-${format}`}.pdf`,
      ]),
    ),
    title: curl(r.title),
    subtitle: curlMaybe(r.subtitle),
    author: curl(r.author),
    translator: curlMaybe(r.translator),
    editor: curlMaybe(r.editor),
    imprint: curl(r.imprint),
    editionNote: curlMaybe(r.edition),
    language: r.language ?? "English",
    publisher: PUBLISHER,
    published: r.published ?? PUBLISHED,
    publicDomain: Boolean(r.publicDomain),
    parts: parts.map((part) => ({
      title: part.title,
      entries: part.entries.map(({ file, label }) => ({
        label,
        heading: firstHeading(file),
      })),
    })),
  };
}
