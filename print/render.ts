/**
 * The print renderer of the books repository: MDX -> print-ready HTML -> PDF
 * (headless Chrome). Shared by every site that shows these texts (botaschool,
 * agelesswisdom) and by the repository's own release build, so a text is set
 * the same wherever it is printed: one lowering, one set of fonts, one
 * stylesheet for the elements.
 *
 * The Markdown is NOT parsed here: `createRenderer` is handed the caller's own
 * MDX pipeline (the same remark and rehype plugins its site runs), stops at
 * the HTML tree, and lowers it for paged media with one small rehype step
 * below. So a construct renders in the PDF exactly as it parses on the web,
 * and a plugin added to the site is picked up here automatically. An earlier
 * hand-rolled line parser had to re-implement every custom tag; that class
 * of drift is gone.
 *
 * What is here: the print-specific lowering (figures, footnotes, symbol
 * spans, the format's tags to plain elements), the vendored fonts, the shared
 * element CSS, and the Chrome call. What the caller supplies (RendererOptions):
 * its pipeline, where an image URL is on disk, and any tags of its own beyond
 * the format's (a site's TarotGroups, say). Page geometry and document
 * furniture (mastheads, running feet) stay with each document kind.
 */
import { createProcessor } from "@mdx-js/mdx";
import type { Element, ElementContent, Root, RootContent } from "hast";
import { toHtml } from "hast-util-to-html";
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { VFile } from "vfile";
import type { ProcessorOptions } from "@mdx-js/mdx";
import {
  TAROT_GRIDS_PER_GROUP,
  TAROT_GROUPS,
  tarotGridNumbers,
} from "./tarot-groups.ts";

// Vendored fonts committed alongside this renderer so the PDF build is
// self-contained and reproducible on any platform (incl. a Linux CI runner).
export const FONTS_DIR = path.join(import.meta.dirname, "fonts");

/** What a caller gives the renderer. */
export interface RendererOptions {
  /** The caller's MDX pipeline, its plugins loaded (unified's shape): the
   *  very plugins its site runs, so the PDF parses as the page does. */
  remarkPlugins: ProcessorOptions["remarkPlugins"];
  rehypePlugins: ProcessorOptions["rehypePlugins"];
  /** Where an image URL in the text (`/images/…`, as the pipeline leaves it)
   *  is on disk, for Chrome to load. */
  asset: (src: string) => string;
  /** Tags of the caller's own beyond the format's, each lowered to elements:
   *  by name, given a function that lowers the tag's children. */
  tags?: Record<string, (children: () => ElementContent[]) => ElementContent[]>;
}

/** The tarot-group tableaus, drawn from the offset tables (tarot-groups.ts). */
function tarotGroupsElement(): Element {
  return el(
    "div",
    { className: ["tarot-groups"] },
    TAROT_GROUPS.map((group) =>
      el("section", { className: ["tarot-group"] }, [
        el("h4", {}, [text(group.name)]),
        ...Array.from({ length: TAROT_GRIDS_PER_GROUP }, (_, i) =>
          el(
            "div",
            { className: ["tarot-grid"] },
            tarotGridNumbers(group, i + 1).map((n) =>
              el("span", {}, [text(String(n))]),
            ),
          ),
        ),
      ]),
    ),
  );
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function roman(value: number): string {
  const numerals: [number, string][] = [
    [1000, "M"],
    [900, "CM"],
    [500, "D"],
    [400, "CD"],
    [100, "C"],
    [90, "XC"],
    [50, "L"],
    [40, "XL"],
    [10, "X"],
    [9, "IX"],
    [5, "V"],
    [4, "IV"],
    [1, "I"],
  ];
  let out = "";
  for (const [n, r] of numerals) {
    while (value >= n) {
      out += r;
      value -= n;
    }
  }
  return out;
}

// ---- MDX -> print HTML ----------------------------------------------------

/** Astrological / planetary glyphs get a span so the symbol font stack (see
 *  .symbol in sharedElementsCss) handles their presentation. */
const SYMBOL = /[♈♉♊♋♌♍♎♏♐♑♒♓☉♀♂♃♄☾☿]/g;

/** hast nodes as they arrive from the MDX pipeline: hast proper, plus the MDX
 *  JSX/expression/ESM nodes that remark-rehype passes through untouched. */
type MdxJsxAttribute = {
  type: "mdxJsxAttribute";
  name: string;
  value?: string | { type: string; value: string } | null;
};
type MdxNode =
  | RootContent
  | {
      type: "mdxJsxFlowElement" | "mdxJsxTextElement";
      name: string | null;
      attributes: MdxJsxAttribute[];
      children: MdxNode[];
    }
  | { type: "mdxFlowExpression" | "mdxTextExpression" | "mdxjsEsm" };

export function el(
  tagName: string,
  properties: Element["properties"],
  children: ElementContent[] = [],
): Element {
  return { type: "element", tagName, properties, children };
}

export function text(value: string): ElementContent {
  return { type: "text", value };
}

/** The options of the render in progress (`mdxToHtml` is synchronous, so
 *  one at a time): the lowering below reads the asset resolver and the
 *  caller's tags from here. */
let active: RendererOptions;

/** Resolve an image URL to the file Chrome should load. */
function assetPath(src: string): string {
  return active.asset(src);
}

/** `alt` carries "description|WIDTHxHEIGHT" (see mdx-components.tsx). */
function imageParts(alt: string): {
  alt: string;
  width?: number;
  height?: number;
} {
  const [description, dims] = alt.split("|");
  if (dims && /^\d+x\d+$/.test(dims)) {
    const [width, height] = dims.split("x").map(Number);
    return { alt: description, width, height };
  }
  return { alt: description ?? "" };
}

/** A paragraph that is nothing but one image becomes a figure; the alt text is
 *  its caption unless it is the generic "Figure". */
function figureFor(img: Element): Element {
  const { alt, width, height } = imageParts(String(img.properties.alt ?? ""));
  const properties: Element["properties"] = {
    src: assetPath(String(img.properties.src ?? "")),
    alt,
  };
  const figureProps: Element["properties"] = { className: ["figure"] };
  if (width && height) {
    properties.width = width;
    properties.height = height;
    figureProps.style = `--aspect:${width}/${height}`;
  }
  const children: ElementContent[] = [el("img", properties)];
  if (alt && alt !== "Figure") {
    children.push(el("figcaption", {}, [text(alt)]));
  }
  return el("figure", figureProps, children);
}

/** remark-gfm's footnote section (an <ol> of notes with back-references) in
 *  the print shape: one `.footnote` paragraph per note, its number as a
 *  superscript, no links — PDFs carry none. */
function footnotesFor(section: Element): Element {
  const notes: ElementContent[] = [];
  const list = section.children.find(
    (c): c is Element => c.type === "element" && c.tagName === "ol",
  );
  for (const li of list?.children ?? []) {
    if (li.type !== "element" || li.tagName !== "li") continue;
    const label = String(li.properties.id ?? "").replace(
      /^user-content-fn-/,
      "",
    );
    // The note's paragraphs, with the "↩" back-reference dropped.
    const body = li.children.flatMap((c) =>
      c.type === "element" && c.tagName === "p" ? c.children : [c],
    );
    const content = lowerAll(body as MdxNode[], false).filter(
      (c) =>
        !(
          c.type === "element" &&
          c.tagName === "a" &&
          "dataFootnoteBackref" in c.properties
        ),
    );
    notes.push(
      el("p", { className: ["footnote"] }, [
        el("sup", {}, [text(label)]),
        text(" "),
        ...content,
      ]),
    );
  }
  return el("div", { className: ["footnotes"] }, notes);
}

/** JSX attributes -> hast properties. JSX names (className, colSpan) ARE the
 *  hast property names; hast-util-to-html spells them as HTML attributes. */
function jsxProperties(
  attributes: ReadonlyArray<{ type: string; name?: string; value?: unknown }>,
): Element["properties"] {
  const properties: Element["properties"] = {};
  for (const attr of attributes) {
    if (attr.type !== "mdxJsxAttribute" || !attr.name) continue;
    const raw =
      attr.value == null
        ? true
        : typeof attr.value === "string"
          ? attr.value
          : String((attr.value as { value: string }).value); // {2} -> "2"
    if (attr.name === "className") {
      properties.className = String(raw).split(/\s+/);
    } else if (attr.name === "colSpan" || attr.name === "rowSpan") {
      properties[attr.name] = Number(raw);
    } else {
      properties[attr.name] = raw;
    }
  }
  return properties;
}

/** Wrap symbol glyphs in `.symbol` spans (not inside code, where text is
 *  verbatim). */
function lowerText(value: string, inCode: boolean): ElementContent[] {
  if (inCode || !SYMBOL.test(value)) return [text(value)];
  SYMBOL.lastIndex = 0;
  const out: ElementContent[] = [];
  let last = 0;
  for (const match of value.matchAll(SYMBOL)) {
    if (match.index > last) out.push(text(value.slice(last, match.index)));
    out.push(el("span", { className: ["symbol"] }, [text(match[0])]));
    last = match.index + match[0].length;
  }
  if (last < value.length) out.push(text(value.slice(last)));
  return out;
}

function lowerAll(nodes: MdxNode[], inCode: boolean): ElementContent[] {
  return nodes.flatMap((node) => lower(node, inCode));
}

/**
 * The print lowering, one node at a time. Returns the replacement(s): a node
 * may become several (a link unwraps to its children) or none (ESM, expressions,
 * footnote back-references).
 */
function lower(node: MdxNode, inCode: boolean): ElementContent[] {
  switch (node.type) {
    case "text":
      return lowerText(node.value, inCode);

    case "element": {
      const { tagName, properties } = node;
      // A link to a place in the same document (an anchor, "#…": an entry
      // of a book's contents, by remark-book-links) stays live in the PDF;
      // any other is just its text.
      if (tagName === "a") {
        if ("dataFootnoteBackref" in properties) return [];
        const href = String(properties.href ?? "");
        if (href.startsWith("#") && !("dataFootnoteRef" in properties)) {
          return [
            el("a", { href }, lowerAll(node.children as MdxNode[], inCode)),
          ];
        }
        return lowerAll(node.children as MdxNode[], inCode);
      }
      if (tagName === "section" && "dataFootnotes" in properties) {
        return [footnotesFor(node)];
      }
      // A paragraph holding only an image is a figure.
      if (tagName === "p") {
        const meaningful = node.children.filter(
          (c) => !(c.type === "text" && c.value.trim() === ""),
        );
        const only = meaningful[0];
        if (
          meaningful.length === 1 &&
          only.type === "element" &&
          only.tagName === "img"
        ) {
          return [figureFor(only)];
        }
      }
      if (tagName === "img") {
        const { alt, width, height } = imageParts(String(properties.alt ?? ""));
        const props: Element["properties"] = {
          className: ["inline-image"],
          src: assetPath(String(properties.src ?? "")),
          alt,
        };
        if (width && height) Object.assign(props, { width, height });
        return [el("img", props)];
      }
      // The lesson title is the masthead's <h1> (see lessons.ts), so body
      // headings sit one level down: `##` in the source is an <h3> here.
      const heading = /^h([1-5])$/.exec(tagName);
      if (heading) {
        const level = Math.min(Number(heading[1]) + 1, 5);
        return [
          el("h" + level, {}, lowerAll(node.children as MdxNode[], inCode)),
        ];
      }
      // GFM column alignment as an inline style (the `align` attribute is
      // obsolete HTML).
      const props: Element["properties"] = { ...properties };
      if ((tagName === "td" || tagName === "th") && props.align) {
        props.style = `text-align:${props.align}`;
        delete props.align;
      }
      const code = inCode || tagName === "code" || tagName === "pre";
      return [el(tagName, props, lowerAll(node.children as MdxNode[], code))];
    }

    case "mdxJsxFlowElement":
    case "mdxJsxTextElement": {
      const children = () => lowerAll(node.children, inCode);
      switch (node.name) {
        // The custom tags, each mirroring its web component in
        // mdx-components.tsx (same class names; the print CSS styles them).
        case "KeepTogether":
          return [el("div", { className: ["keep-together"] }, children())];
        case "EditorNote":
          return [el("p", { className: ["editor-note"] }, children())];
        case "EditorGap":
          return [el("span", { className: ["editor-note"] }, children())];
        case "Center":
          return [el("p", { className: ["centered"] }, children())];
        case "Right":
          return [el("p", { className: ["right-set"] }, children())];
        case "Rule":
          return [el("hr", { className: ["short-rule"] }, [])];
        case "Cite":
          return [
            el("p", { className: ["quote-cite"] }, [text("— "), ...children()]),
          ];
        case "TarotGroups":
          return [tarotGroupsElement()];
      }
      // The caller's own tags.
      const own = node.name ? active.tags?.[node.name] : undefined;
      if (own) return own(children);
      // Hand-written HTML in the MDX (<div className=…>, <table>, <br />,
      // <sup>): the same element, attributes normalized.
      if (node.name && /^[a-z]/.test(node.name)) {
        return [el(node.name, jsxProperties(node.attributes), children())];
      }
      throw new Error(
        `print: no rendering for <${node.name ?? "fragment"}> — a tag of the ` +
          `format is lowered in lower() (books/print/render.ts); a site's own ` +
          `is given in RendererOptions.tags.`,
      );
    }

    // import/export lines and {expressions}: nothing to print.
    case "mdxFlowExpression":
    case "mdxTextExpression":
    case "mdxjsEsm":
      return [];

    default:
      return [node as ElementContent];
  }
}

const isElement = (node: ElementContent | undefined): node is Element =>
  node?.type === "element";
const hasClass = (node: Element, name: string) =>
  ([] as unknown[]).concat(node.properties.className ?? []).includes(name);

/**
 * Keep every quotation's attribution on the same page as the end of the quote.
 *
 * `break-before: avoid` on the citation is NOT enough: Chrome would have to
 * break inside the blockquote, one level up, and it doesn't look that far —
 * measured stranding a citation alone at the top of a page at 17 of 40 page
 * positions. So the citation moves INTO the blockquote and is wrapped with
 * the quote's last paragraph in one `.quote-end` block that can't be split:
 * both fit on this page, or both go to the next. 0 of 40 strand this way.
 */
function bindCitations(children: ElementContent[]): ElementContent[] {
  const out: ElementContent[] = [];
  for (const node of children) {
    if (isElement(node)) node.children = bindCitations(node.children);
    if (
      isElement(node) &&
      node.tagName === "p" &&
      hasClass(node, "quote-cite")
    ) {
      const prev = [...out]
        .reverse()
        .find((n) => !(n.type === "text" && n.value.trim() === ""));
      if (isElement(prev) && prev.tagName === "blockquote") {
        const lastIndex = prev.children.findLastIndex(isElement);
        if (lastIndex >= 0) {
          const last = prev.children[lastIndex];
          prev.children.splice(
            lastIndex,
            1,
            el("div", { className: ["quote-end"] }, [last, node]),
          );
          continue;
        }
      }
    }
    out.push(node);
  }
  return out;
}

/** Captured by the plugin below on each run; `mdxToHtml` reads it back. A
 *  module-level slot is the plain way for a unified plugin to return a value. */
let printed = "";

/** The last rehype step: lower the site's HTML tree for print and serialize
 *  it. Everything after this stage in the MDX processor (JSX compilation)
 *  still runs and is ignored. */
function rehypePrint() {
  return (tree: Root) => {
    const children = bindCitations(lowerAll(tree.children as MdxNode[], false));
    printed = toHtml({ type: "root", children } as Root);
  };
}

export interface Renderer {
  /**
   * MDX -> print HTML fragment, through the caller's own pipeline.
   *
   * `path` is the file's path, for the plugins that key on it (the Books'
   * figures are resolved from theirs); without one, nothing path-bound
   * runs. A site's paragraph-anchor plugin, say, keys on `content/lessons/`
   * and would otherwise add its ¶ markers, a web affordance. Synchronous,
   * so the print builders and the editorial tools can stay simple loops.
   */
  mdxToHtml(markdown: string, path?: string): string;
}

/** A renderer running the caller's pipeline. */
export function createRenderer(options: RendererOptions): Renderer {
  const processor = createProcessor({
    remarkPlugins: options.remarkPlugins,
    rehypePlugins: [...(options.rehypePlugins ?? []), rehypePrint],
  });
  return {
    mdxToHtml(markdown, path) {
      active = options;
      const file = new VFile({ value: markdown, path });
      processor.runSync(processor.parse(file) as never, file);
      return printed;
    },
  };
}

/** @font-face blocks for every script the lessons use. The governing rule:
 *  EVERY glyph in the content must resolve to a vendored, OFL-licensed, STATIC
 *  font that is committed to the repo — so the PDF embeds only fonts we may
 *  redistribute, renders identically on macOS and the Linux CI runner, and
 *  never silently falls back to a system font (Times/Hiragino/…) or embeds a
 *  variable font as Type 3 (which Chrome does, and POD preflights flag).
 *
 *  The lessons mix Latin, Greek (Θ = alchemical Salt) and polytonic Greek (ὕ),
 *  Hebrew (many lessons), astrological + alchemical symbols, and math operators
 *  (∇ = alchemical Water). Each gets an explicit face here. Two subtleties make
 *  it robust rather than whack-a-mole:
 *    • Greek rides the same "Print Literata" family via unicode-range so it
 *      stays visually seamless — but the ranges MUST be disjoint from the
 *      polytonic faces, because a face that DECLARES a range it doesn't actually
 *      cover blocks fallback for those glyphs (that silently dropped ὕ once).
 *    • Coverage of unwrapped symbols is guaranteed by putting the symbol
 *      families in the body font stack (see lessons.ts / build.ts), not by the
 *      .symbol wrapper alone. The wrapper only handles text-vs-emoji presentation.
 *  Verified after each render with `pdffonts` (expect zero Type 3, zero system
 *  fonts) and `pdfminer` (no glyph drawn from an un-vendored font). */
/** The body font stack every print document uses: Literata first, then the
 *  scripts and symbols it lacks, each a vendored family (fontFaceCss). */
export const FONT_STACK =
  '"Print Literata", "Print Hebrew", "Print Math", "Print Symbols", "Print Symbols 2", "Print Marks", serif';

export function fontFaceCss(): string {
  const f = (name: string) => path.join(FONTS_DIR, name);
  return `
@font-face {
  font-family: "Print Symbols";
  src: url("${f("NotoSansSymbols-Regular.ttf")}") format("truetype");
}
/* Misc symbols the primary Noto Sans Symbols lacks (☉ SUN, alchemical block
   🜁🜂🜃…) — a second FAMILY, reached by cross-family fallback when the first
   genuinely lacks the glyph. */
@font-face {
  font-family: "Print Symbols 2";
  src: url("${f("NotoSansSymbols2.woff2")}") format("woff2");
}
/* Math operators (∇ = alchemical Water sign, △▽) — Noto Sans Math. */
@font-face {
  font-family: "Print Math";
  src: url("${f("NotoSansMath-Regular.woff2")}") format("woff2");
}
/* Hebrew — Noto Serif Hebrew, matched to Literata's serif register. */
@font-face {
  font-family: "Print Hebrew";
  src: url("${f("NotoSerifHebrew-Regular.woff2")}") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Print Hebrew";
  src: url("${f("NotoSerifHebrew-SemiBold.woff2")}") format("woff2");
  font-weight: 600;
}
/* One combining mark Literata lacks, U+032E (breve below, in Stenring's
   transliteration "Ij̮ar"), with the letters it sits on: Noto Serif, subset
   to j, a and the mark (Google Fonts' text= parameter). Its own family, last
   in the stack: Chrome sets a letter and its mark from ONE font, so the
   fallback for the cluster must hold both, and a face declared for the mark
   alone within Literata's family would never be chosen. */
@font-face {
  font-family: "Print Marks";
  src: url("${f("NotoSerif-Marks.woff2")}") format("woff2");
}
/* Latin — static Literata instances (NOT the variable src/app copy: Chrome
   embeds a variable font as Type 3). */
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-Regular.woff2")}") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-Italic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 400;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-SemiBold.woff2")}") format("woff2");
  font-weight: 600;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-Bold.woff2")}") format("woff2");
  font-weight: 700;
}
/* Bold italic (bold within a quotation, which is set italic): without a
   face of its own Chrome fakes it from the italic and embeds that as Type 3. */
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-BoldItalic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 700;
}
/* Latin Extended (š in Stenring's transliterations) — same family via
   unicode-range (Google Fonts' latin-ext range), disjoint from the rest. */
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-LatinExt.woff2")}") format("woff2");
  font-weight: 400;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-LatinExt-Italic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 400;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-LatinExt-SemiBold.woff2")}") format("woff2");
  font-weight: 600;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-LatinExt-Bold.woff2")}") format("woff2");
  font-weight: 700;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-LatinExt-BoldItalic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 700;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
/* Greek (Θ) — same family via unicode-range. Range must be disjoint from the
   polytonic faces below. */
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-Greek.woff2")}") format("woff2");
  font-weight: 400;
  unicode-range: U+0370-03FF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-Greek-Italic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 400;
  unicode-range: U+0370-03FF;
}
/* Polytonic Greek (Greek Extended, e.g. ὕ). */
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-GreekExt.woff2")}") format("woff2");
  font-weight: 400;
  unicode-range: U+1F00-1FFF;
}
@font-face {
  font-family: "Print Literata";
  src: url("${f("Literata-GreekExt-Italic.woff2")}") format("woff2");
  font-style: italic;
  font-weight: 400;
  unicode-range: U+1F00-1FFF;
}`.trim();
}

/**
 * Styling for the body-level content elements shared by every print artifact
 * (block quotes, tables, figures, symbols, lists, the tarot-groups grid). Page
 * geometry, base type scale, and document furniture stay with each builder.
 */
export function sharedElementsCss(): string {
  return `
/* Block quotations are set off by symmetric indentation + smaller italic
 * (classic book treatment) rather than a left rule. A bordered box that
 * breaks across a page extends its rule down to the page boundary (paged-media
 * box-decoration-break: slice), leaving an awkward hanging line into the void;
 * indentation never does. */
/* A line set centred in the source (<Center>). */
.centered {
  text-align: center;
}
/* A line set to the right in the source (<Right>). */
.right-set {
  text-align: right;
}
/* A short rule set centred in the source (<Rule />). */
hr.short-rule {
  width: 0.6in;
  margin: 0.12in auto;
  border: 0;
  border-top: 0.5pt solid #8a8478;
}
blockquote {
  color: #3f3a31;
  font-size: 0.94em;
  font-style: italic;
  line-height: 1.42;
  margin: 0.18in 0.34in;
}
blockquote p {
  break-inside: avoid;
  orphans: 3;
  text-align: left;
  widows: 3;
}
blockquote p + p {
  margin-top: 0.14in;
}
/* Quoted verse: each line starts flush and only its turnover (wrapped) part
   hangs (professional poetry setting). Same rule as the web; each line is its
   own .verse-line block (plugins/rehype-verse-lines.mjs). */
blockquote .verse-line {
  display: block;
  padding-left: 1.5em;
  text-indent: -1.5em;
}
/* Fenced monospace blocks — the Oracle-of-Tarot aligned attribution lists,
 * card spreads and dot figures. white-space: pre keeps their column alignment;
 * a monospace face at a small size keeps the lines on the page. The pale panel
 * matches the web (gray-100 behind pre in src/app/typography.css) so a printed
 * lesson reads like its page — warmed to the print palette's own family (the
 * lightest tint of the #bdb4a3 / #d9d1c2 rules) rather than the web's cool
 * gray, which read blue against the cream page. print-color-adjust: exact is
 * required — without it Chrome drops background fills when printing, since
 * "background graphics" is off by default. */
pre {
  background-color: #f5f2ea;
  border-radius: 0.05in;
  break-inside: avoid;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 8.5pt;
  line-height: 1.35;
  margin: 0.16in 0;
  padding: 0.09in 0.12in;
  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;
  white-space: pre;
}
pre code {
  font-family: inherit;
}
ol,
ul {
  margin: 0.12in 0 0.12in 0.26in;
  padding: 0;
}
.keep-together {
  break-inside: avoid;
  page-break-inside: avoid;
}
li {
  margin: 0.035in 0;
  padding-left: 0.04in;
}
/* Close a list clearly: the gap before the next paragraph is larger than the
 * space between items, so the list reads as "ended". Covers plain lists
 * (ol/ul directly before a paragraph) and lists wrapped in a keep-together
 * block (where the following paragraph is the block's sibling). */
ol + p,
ul + p,
.keep-together + p {
  margin-top: 0.24in;
}
/* Borders are drawn with border-collapse: SEPARATE (not collapse): the table
   owns the top+left edges, each cell owns its right+bottom, so every grid line
   sits wholly INSIDE an element box. Under collapse the outer border straddles
   the table's box edge instead, putting half of it outside — which needs a
   wider safety inset to survive the page-edge clip that the body rule
   compensates for (see scripts/print/lessons.ts), and shaved the
   right & bottom rules on the web for the same reason. Mirrors the table rules
   in src/app/typography.css. */
table {
  border-collapse: separate;
  border-spacing: 0;
  border-left: 1pt solid #bdb4a3;
  border-top: 1pt solid #bdb4a3;
  break-inside: avoid;
  font-size: 0.92em;
  margin: 0.16in auto;
  max-width: 100%;
  page-break-inside: avoid;
}
/* Columns that are parallel bodies of prose (the Well-dignified /
   Ill-dignified dignity tables) split the width evenly instead of sizing to
   whichever side is wordier. Mirrors the .even-columns rule in typography.css. */
.even-columns table {
  table-layout: fixed;
  width: 100%;
}
td,
th {
  border-bottom: 1pt solid #bdb4a3;
  border-right: 1pt solid #bdb4a3;
  padding: 0.035in 0.055in;
  text-align: center;
  vertical-align: middle;
}
/* Markdown renders a table's first row as <th>, which browsers bold by
   default; most lesson tables are data grids with no real header. Same rule
   as the web (typography.css): a header is bold only when its cells are
   bolded explicitly (**Header**). */
th {
  font-weight: inherit;
}
figure {
  break-inside: avoid;
  margin: 0.2in auto;
  max-width: 100%;
  text-align: center;
}
figure img {
  height: auto;
  max-height: 6.35in;
  max-width: 100%;
  object-fit: contain;
}
figcaption {
  color: #766f61;
  font-size: 0.84em;
  font-style: italic;
  margin-top: 0.05in;
}
/* Editorial apparatus (the editors' voice, not Case's text) — matches the
   figcaption secondary tone. Set by the EditorNote component / <EditorNote> tag. */
.editor-note {
  color: #766f61;
  font-size: 0.84em;
  font-style: italic;
}
/* Quotation source attribution — muted, right-aligned, roman (contrasting the
   italic blockquote). Scoped under .lesson-body to beat the justify rule on
   .lesson-body p. bindCitations() moves it into its blockquote, bound to the
   quote's last paragraph in an unbreakable .quote-end, so it can never be
   stranded on the next page. */
.quote-end {
  break-inside: avoid;
  page-break-inside: avoid;
}
/* The last paragraph keeps its usual gap from the one before it. */
blockquote > * + .quote-end {
  margin-top: 0.14in;
}
/* Inside the blockquote, undo the quote's own inset and smaller size so the
   attribution still aligns with the text column at its normal size. */
.lesson-body blockquote .quote-cite {
  font-size: calc(0.9em / 0.94);
  margin-right: -0.34in;
}
.lesson-body .quote-cite {
  /* Fallback for a citation after a plain paragraph, which bindCitations()
     leaves alone. */
  break-before: avoid;
  page-break-before: avoid;
  color: #766f61;
  font-size: 0.9em;
  font-style: normal;
  margin-top: 0.06in;
  text-align: right;
}
.inline-image {
  display: inline-block;
  max-height: 1em;
  max-width: 1.2em;
  object-fit: contain;
  vertical-align: -0.12em;
}
.symbol {
  /* Second symbol family (☉ etc.) via cross-family fallback; no system font in
     the chain so a wrapped glyph can never reach an unembedded/unlicensed face. */
  font-family: "Print Symbols", "Print Symbols 2", "Print Literata";
  font-variant-emoji: text;
}
.tarot-groups {
  display: flex;
  flex-direction: column;
  gap: 0.18in;
  margin: 0.16in 0;
}
.tarot-group {
  break-inside: avoid;
  display: grid;
  gap: 0.055in;
  grid-template-columns: repeat(4, 1fr);
}
.tarot-group h4 {
  align-self: center;
  font-size: 0.85em;
  letter-spacing: 0.03em;
  margin: 0;
  text-align: center;
  text-transform: uppercase;
}
.tarot-grid {
  border: 0.35pt solid #bdb4a3;
  display: grid;
  font-size: 0.78em;
  grid-template-columns: repeat(3, 1fr);
  line-height: 1.25;
}
.tarot-grid span {
  border: 0.25pt solid #d9d1c2;
  padding: 0.012in 0;
  text-align: center;
}
/* End-of-lesson notes: a classic short separator rule, then the collected
 * footnotes in smaller muted type. Kept whole — a split note reads badly and
 * the blocks are always short. */
.footnotes {
  break-inside: avoid;
  margin-top: 0.32in;
}
.footnotes::before {
  border-top: 1pt solid #bdb4a3;
  content: "";
  display: block;
  margin-bottom: 0.1in;
  width: 2.2in;
}
.footnote {
  color: #4a4438;
  font-size: 0.86em;
  line-height: 1.35;
  margin: 0.08in 0;
  text-align: left;
}
.footnote sup {
  margin-right: 0.28em;
}`.trim();
}

function chromePath(): string {
  // CHROME_BIN escape hatch for CI / non-standard installs.
  if (process.env.CHROME_BIN) return process.env.CHROME_BIN;
  const macChrome =
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (fs.existsSync(macChrome)) return macChrome;
  // On the GitHub ubuntu runner (and most Linux setups) this is on PATH;
  // execFileSync resolves it via PATH.
  return "google-chrome";
}

export function buildPdf(
  htmlPath: string,
  pdfPath: string,
  { outline = false }: { outline?: boolean } = {},
) {
  // `--print-to-pdf` is fire-and-forget: Chrome prints the moment it considers
  // the page "loaded", which does NOT guarantee the @font-face web fonts have
  // finished loading and re-laid-out the text. On a fast local disk the fonts
  // win the race and every page is perfect; on the slower CI runner the print
  // can fire mid-layout, dropping whole body paragraphs (blockquotes, being
  // shorter, survive) and leaving blank pages — the exact macOS-fine / Linux-
  // broken divergence we hit. The fix, all supported by the plain CLI:
  //   • --virtual-time-budget advances a virtual clock and HOLDS the print
  //     until pending resources (the fonts) settle or the budget elapses — the
  //     canonical cure for the print-before-fonts race.
  //   • --run-all-compositor-stages-before-draw forces a full paint first.
  //   • --headless=new is the maintained headless implementation (old headless
  //     is being removed from Chrome and renders paged media inconsistently).
  execFileSync(chromePath(), [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    // No glyph hinting on Linux, where Chrome would otherwise hint by
    // default: the glyphs are set the same there as on macOS, which never
    // hints. (The Type 3 fonts Linux builds once embedded were Chrome's
    // version, not hinting: 131 embedded every web font as Type 3, 156
    // embeds the fonts themselves. The workflow pins the version.)
    "--font-render-hinting=none",
    "--no-pdf-header-footer",
    // A book's outline (the viewer's bookmarks) from its headings.
    ...(outline ? ["--generate-pdf-document-outline"] : []),
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=20000",
    `--print-to-pdf=${pdfPath}`,
    `file://${htmlPath}`,
  ]);
}
