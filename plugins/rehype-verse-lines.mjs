/**
 * Splits quoted verse into one element per line, so each line can carry its
 * own hanging indent.
 *
 * Lesson verse is written as a blockquote paragraph with a `<br />` after each
 * line. CSS cannot style "the line after a <br>": `text-indent` reaches only
 * the first line of a block, so a hanging indent on the paragraph pushed EVERY
 * line after the first to the right. This wraps each line in
 * `<span class="verse-line">` (a block, see typography.css and the print CSS)
 * and drops the `<br>`s, which the blocks make redundant.
 *
 * Runs in the format's pipeline (mdx.mjs), so a site, its search index
 * and the PDFs all see the same structure. Paragraph anchors are unaffected:
 * the change is INSIDE a blockquote's paragraph, and the anchor plugin only
 * numbers top-level blocks. Text is unchanged, so search is too.
 */

/** In MDX, a hand-written `<br />` arrives as a JSX node, not an element. */
function isBreak(node) {
  return (
    (node.type === "element" && node.tagName === "br") ||
    (node.type === "mdxJsxTextElement" && node.name === "br")
  );
}

function isBlank(node) {
  return node.type === "text" && node.value.trim() === "";
}

function splitVerse(p) {
  if (!p.children.some(isBreak)) return;
  const lines = [[]];
  for (const child of p.children) {
    if (isBreak(child)) lines.push([]);
    else lines[lines.length - 1].push(child);
  }
  p.children = lines
    .map((line) => {
      // The source newline after each <br /> leads the next line; keep it
      // as a separating space so copied text and the search index still see
      // a word boundary, but not as leading whitespace in the box.
      while (line.length && isBlank(line[0])) line.shift();
      if (line[0]?.type === "text")
        line[0] = { ...line[0], value: line[0].value.replace(/^\s+/, "") };
      return line;
    })
    .filter((line) => line.length > 0)
    .flatMap((line, i) => [
      ...(i > 0 ? [{ type: "text", value: "\n" }] : []),
      {
        type: "element",
        tagName: "span",
        properties: { className: ["verse-line"] },
        children: line,
      },
    ]);
}

function walk(node, inQuote) {
  for (const child of node.children ?? []) {
    if (child.type !== "element") {
      if (child.children) walk(child, inQuote);
      continue;
    }
    if (inQuote && child.tagName === "p") splitVerse(child);
    walk(child, inQuote || child.tagName === "blockquote");
  }
}

export default function rehypeVerseLines() {
  return (tree) => walk(tree, false);
}
