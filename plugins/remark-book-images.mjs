// A text's figures live in its edition's `images/` and are referenced
// relative to the file that shows them (<work>/<edition>/03.mdx says
// `images/wheel.png`; a part's <work>/<edition>/<part>/03.mdx says
// `../images/<part>/fig.jpeg`; the README). Every relative image URL in a
// file under the books root is pointed at where the consumer serves (or
// reads) that edition's images: `base`, with {work} and {edition} filled
// in, then the path under `images/`. A site passes its URL
// ("/images/books/{work}/{edition}"); the repository's own print build
// passes the folder on disk. Absolute URLs, files outside the root, and
// references outside the edition's images/ are left alone.

import path from "node:path";
import { visit } from "unist-util-visit";

/**
 * @param {{ root: string, base: string }} options
 *   root: the books root (the folder holding the works), absolute;
 *   base: where an edition's images are, with {work} and {edition}.
 */
export default function remarkBookImages({ root, base }) {
  const prefix = root.endsWith(path.sep) ? root : root + path.sep;
  return (tree, file) => {
    const filePath = file?.path ?? "";
    if (!filePath.startsWith(prefix)) return;
    const [work, edition] = filePath.slice(prefix.length).split(path.sep);
    if (!work || !edition) return;
    const images = path.join(prefix, work, edition, "images");
    const at = base.replace("{work}", work).replace("{edition}", edition);
    visit(tree, "image", (node) => {
      if (/^(\/|[a-z]+:)/i.test(node.url)) return;
      const rel = path.relative(
        images,
        path.resolve(path.dirname(filePath), node.url),
      );
      if (rel.startsWith("..")) return;
      node.url = `${at}/${rel.split(path.sep).join("/")}`;
    });
  };
}
