// A link within a text, to an entry of its contents or to a part, is
// written relative to the edition (the README): `03.mdx`,
// `../section-a/09.mdx#p12`, `../section-b/`. Every such link in a file
// under the books root is pointed at where the consumer shows that entry
// or part: the `entry` and `part` templates, with {work}, {edition}, {part}
// (the part's folder; nothing, and the `/` or `-` after it dropped, for a
// book without parts), {n} (the entry's number, unpadded) and {fragment}
// (the link's own `#p12`, or nothing) filled in. A site passes its
// addresses ("/{part}/lesson-{n}{fragment}"); the repository's own print
// build passes anchors within the document ("#{part}-{n}"). Absolute URLs,
// fragments alone, and relative links that are not an entry or a part of
// the same edition are left alone.

import fs from "node:fs";
import path from "node:path";
import { visit } from "unist-util-visit";

/**
 * @param {{ root: string, entry: string, part: string }} options
 *   root: the books root (the folder holding the works), absolute;
 *   entry: the address of an entry; part: of a part (templates, above).
 */
export default function remarkBookLinks({ root, entry, part }) {
  const prefix = root.endsWith(path.sep) ? root : root + path.sep;
  return (tree, file) => {
    const filePath = file?.path ?? "";
    if (!filePath.startsWith(prefix)) return;
    const [work, edition] = filePath.slice(prefix.length).split(path.sep);
    if (!work || !edition) return;
    const editionDir = path.join(prefix, work, edition);
    visit(tree, "link", (node) => {
      if (/^(\/|#|[a-z]+:)/i.test(node.url)) return;
      const hash = node.url.indexOf("#");
      const target = hash < 0 ? node.url : node.url.slice(0, hash);
      const fragment = hash < 0 ? "" : node.url.slice(hash);
      if (!target) return;
      const rel = path
        .relative(editionDir, path.resolve(path.dirname(filePath), target))
        .split(path.sep)
        .join("/");
      if (rel.startsWith("..")) return;
      const own = path.relative(editionDir, path.dirname(filePath)).split(path.sep)[0] || "";
      const asEntry = /^(?:([^/]+)\/)?(\d{2})\.mdx$/.exec(rel);
      if (asEntry) {
        const n = String(Number(asEntry[2]));
        node.url = fillTemplate(entry, { work, edition, part: asEntry[1] ?? own, n, fragment });
        return;
      }
      if (
        /^[^/]+$/.test(rel) &&
        fs.existsSync(path.join(editionDir, rel, "01.mdx"))
      ) {
        node.url = fillTemplate(part, { work, edition, part: rel, n: "", fragment });
      }
    });
  };
}

/** The template filled; `{part}` with the `/` or `-` after it goes when
 *  there is no part. */
function fillTemplate(template, values) {
  const withPart = values.part
    ? template
    : template.replace(/\{part\}[/-]?/g, "");
  return withPart.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}
