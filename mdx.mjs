/**
 * The format's MDX pipeline, defined once, for every consumer: a site's
 * pages, its search index, and the print renderer (print/render.ts) build
 * their processor from this, so a construct parses the same everywhere.
 *
 * Plugins are named as [specifier, options] rather than imported functions
 * because a Next.js config needs them SERIALIZABLE (Turbopack); options are
 * plain data for the same reason. `loadMdxPlugins` resolves the specifiers
 * with dynamic import for the consumers that want functions. A site adds
 * its own plugins after these (botaschool its paragraph anchors, a web
 * affordance).
 *
 *   remark-gfm           tables, footnotes
 *   remark-smartypants   typographic quotes, dashes, ellipses; `inverted`
 *                        makes `--` an em dash (Case's typewriter convention)
 *   remark-book-images   a text's figures, by a path relative to the file
 *   remark-book-links    links within a text (to an entry of its contents,
 *                        or a part), relative to the edition, to where the
 *                        consumer shows them (only when `links` is given)
 *   rehype-verse-lines   quoted verse, a `<br />` after each line, one block
 *                        per line (see its header)
 */

const here = (file) => new URL(file, import.meta.url).pathname;

/**
 * @param {{ booksRoot: string, imageBase: string, links?: { entry: string, part: string } }} options
 *   booksRoot: the folder holding the works, absolute (`books/`; a site:
 *     that folder in its submodule);
 *   imageBase: where an edition's images are served or read, with {work}
 *     and {edition} ("/images/books/{work}/{edition}");
 *   links: where an entry of a text's contents, and a part, are shown,
 *     templates with {work}, {edition}, {part}, {n}, {fragment}
 *     (plugins/remark-book-links.mjs); absent, such links stay as written.
 */
export function basePlugins({ booksRoot, imageBase, links }) {
  return {
    remark: [
      ["remark-gfm"],
      ["remark-smartypants", { dashes: "inverted", backticks: false }],
      [here("./plugins/remark-book-images.mjs"), { root: booksRoot, base: imageBase }],
      ...(links
        ? [[here("./plugins/remark-book-links.mjs"), { root: booksRoot, ...links }]]
        : []),
    ],
    rehype: [[here("./plugins/rehype-verse-lines.mjs")]],
  };
}

/** The specs as unified plugins (dynamic import of each specifier). */
export async function loadMdxPlugins(specs) {
  return Promise.all(
    specs.map(async ([specifier, options]) => {
      const mod = await import(specifier);
      return options === undefined ? mod.default : [mod.default, options];
    }),
  );
}
