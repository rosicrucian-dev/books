# print

The renderer that sets these texts for print, shared by every site that
shows them and by this repository's own release build, so a text looks the
same wherever it is printed. TypeScript, run with Node's own type
stripping (`node --experimental-strip-types`); the dependencies are in
`package.json`, and a site that holds this repository as a submodule
already has them.

What it does: a caller's MDX pipeline parses the text (the same plugins
its site runs, so the PDF parses as the page does); `render.ts` stops at
the HTML tree and lowers it for paged media (figures with their captions,
footnotes as notes, the symbol glyphs in their font, the format's tags to
plain elements), gives the `@font-face` rules for the vendored fonts in
`fonts/` and the stylesheet for the elements, and prints an HTML file to
PDF with headless Chrome.

```ts
import { createRenderer, buildPdf, fontFaceCss, sharedElementsCss } from "<this folder>/render.ts";

const renderer = createRenderer({
  remarkPlugins,          // the site's, loaded
  rehypePlugins,
  asset: (src) => ...,    // where an image URL is on disk
  tags: { TarotGroups: () => [...] },  // the site's own tags, if any
});
const body = renderer.mdxToHtml(markdown, pathOfTheFile);
// wrap it in a document with fontFaceCss() + sharedElementsCss() + the
// document kind's own page geometry, then
buildPdf(htmlPath, pdfPath);
```

Page geometry, mastheads and running feet belong to each document kind
(a lesson, a book, a bound volume), not here. The book is `book.ts`: an
edition's folder to one document, US Letter on the lessons' page and type,
a title page from book.json, the text's contents a file each (every one
on a fresh page under its label), and where they are gathered in parts, a
page for each part's title and its contents set one level down; the
outline from the headings (part, entry, the text's own). The editors' note
and the colophon are not printed for now, while the notes are rewritten. `build.ts`
sets every edition that way into `dist/` (`npm run pdf` at the root; the
pipeline from `../mdx.mjs`, the figures read from each folder). A book never gets its own
renderer or stylesheet: a construct one book has that the format cannot
say becomes a tag of the format, lowered here and handled by every
consumer.

Fonts: Literata (static instances, regular, italic, semibold, bold and
bold italic; a variable font, or a weight Chrome has to fake, it would
embed as Type 3; Latin, Latin Extended, Greek and polytonic Greek faces), Noto
Serif Hebrew, Noto Sans Symbols and Symbols 2, Noto Sans Math, and Noto
Serif subset to the breve below (U+032E) with the letters it sits on; all
OFL. `FONT_STACK` is the body stack a document uses. Every glyph in a text must resolve to one of them, so the
PDF embeds only fonts that may be redistributed and renders the same on
every machine. Check a render with `pdffonts` (no Type 3, no system font).

Chrome: Google Chrome on macOS, `google-chrome` on PATH elsewhere, or
`CHROME_BIN`.
