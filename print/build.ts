/**
 * Sets every edition in the repository as a PDF (the release build), or
 * those named:
 *
 *   npm run pdf                         every edition -> dist/<work>-<edition>.pdf
 *                                       (dist/<work>.pdf for a standalone work),
 *                                       and its screen edition beside it,
 *                                       dist/<name>-screen.pdf (book.ts)
 *   npm run pdf -- kybalion/1908        one
 *   npm run pdf -- --html-only          the HTML only (dist/html/), no Chrome
 *
 * Every run also writes dist/catalog.json (catalog.ts): what each edition
 * built is, for the sites that list the books.
 *
 * Run from the repository with its dependencies installed (`npm install`).
 * The pipeline is the format's (mdx.mjs), figures read from each edition's
 * folder; the renderer print/render.ts; the document print/book.ts.
 */
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { basePlugins, loadMdxPlugins } from "../mdx.mjs";
import { PAGE_FORMATS, bookDocumentHtml, readBook } from "./book.ts";
import { type CatalogBook, catalogBook } from "./catalog.ts";
import { buildPdf, createRenderer } from "./render.ts";

const ROOT = path.join(import.meta.dirname, "..");
/** The folder holding the works (the README). */
export const BOOKS = path.join(ROOT, "books");
const DIST = path.join(ROOT, "dist");

export interface Edition {
  work: string;
  edition: string;
  /** The PDF's name: the work and the edition (whose translation, which
   *  printing), or the work alone for a standalone work (work.json). */
  name: string;
}

/** Every edition: books/<work>/<edition>/book.json under a <work>/work.json. */
export function allEditions(): Edition[] {
  const out: Edition[] = [];
  for (const work of fs.readdirSync(BOOKS).sort()) {
    const record = path.join(BOOKS, work, "work.json");
    if (!fs.existsSync(record)) continue;
    const { standalone } = JSON.parse(fs.readFileSync(record, "utf8")) as {
      standalone?: boolean;
    };
    for (const edition of fs.readdirSync(path.join(BOOKS, work)).sort()) {
      if (!fs.existsSync(path.join(BOOKS, work, edition, "book.json"))) continue;
      out.push({ work, edition, name: standalone ? work : `${work}-${edition}` });
    }
  }
  return out;
}

function revision(): string {
  try {
    return execFileSync(
      "git",
      // Not the rolling `latest` tag the release workflow moves along main.
      ["describe", "--always", "--dirty", "--tags", "--exclude=latest"],
      { cwd: ROOT, encoding: "utf8" },
    ).trim();
  } catch {
    return "unknown";
  }
}

async function main() {
  const args = process.argv.slice(2);
  const htmlOnly = args.includes("--html-only");
  const only = args.filter((a) => !a.startsWith("--"));
  const editions = allEditions().filter(
    (e) => !only.length || only.includes(`${e.work}/${e.edition}`),
  );
  if (!editions.length) throw new Error(`no edition matches ${only.join(" ")}`);

  const base = basePlugins({
    booksRoot: BOOKS,
    imageBase: path.join(BOOKS, "{work}", "{edition}", "images"),
    // Links within a text go to the entry's page in the same document.
    links: { entry: "#{part}-{n}", part: "#{part}" },
  });
  const renderer = createRenderer({
    remarkPlugins: await loadMdxPlugins(base.remark),
    rehypePlugins: await loadMdxPlugins(base.rehype),
    asset: (src) => src, // already a path on disk (imageBase)
  });
  const rev = revision();
  const date = new Date().toISOString().slice(0, 10);

  fs.mkdirSync(path.join(DIST, "html"), { recursive: true });
  const catalog: CatalogBook[] = [];
  for (const { work, edition, name } of editions) {
    catalog.push(catalogBook(BOOKS, work, edition, name));
    const { record } = readBook({ root: BOOKS, work, edition });
    // The PDF's own properties (render.ts): what a viewer shows and a
    // search engine reads.
    const info = {
      title: record.title,
      author: record.author,
      subject: [record.subtitle, record.edition].filter(Boolean).join(". "),
    };
    for (const format of PAGE_FORMATS) {
      // The print edition keeps the plain name: it is the address every
      // existing link to a PDF already uses.
      const file = format === "print" ? name : `${name}-${format}`;
      const html = path.join(DIST, "html", `${file}.html`);
      fs.writeFileSync(
        html,
        bookDocumentHtml({ root: BOOKS, work, edition, renderer, revision: rev, date, format }),
      );
      if (!htmlOnly) {
        buildPdf(html, path.join(DIST, `${file}.pdf`), { outline: true, info });
      }
      console.log(`${htmlOnly ? "html" : "pdf "} ${file}`);
    }
  }
  // Only the editions built, when some are named: a partial run is for
  // looking at, and the release builds them all.
  fs.writeFileSync(
    path.join(DIST, "catalog.json"),
    `${JSON.stringify({ books: catalog }, null, 2)}\n`,
  );
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
