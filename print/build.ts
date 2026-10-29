/**
 * Sets every edition in the repository as a PDF (the release build), or
 * those named:
 *
 *   npm run pdf                         every edition -> dist/<work>-<edition>.pdf
 *                                       (dist/<work>.pdf for a standalone work)
 *   npm run pdf -- kybalion/1908        one
 *   npm run pdf -- --html-only          the HTML only (dist/html/), no Chrome
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
import { bookDocumentHtml } from "./book.ts";
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
  for (const { work, edition, name } of editions) {
    const html = path.join(DIST, "html", `${name}.html`);
    fs.writeFileSync(
      html,
      bookDocumentHtml({ root: BOOKS, work, edition, renderer, revision: rev, date }),
    );
    if (!htmlOnly) buildPdf(html, path.join(DIST, `${name}.pdf`), { outline: true });
    console.log(`${htmlOnly ? "html" : "pdf "} ${name}`);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
