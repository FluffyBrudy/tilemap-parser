import { FLAT } from "../src/nav";

export type IndexSection = { id: string; head: string; text: string };
export type IndexPage = {
  route: string;
  title: string;
  sections: IndexSection[];
};

const NAV_LABELS = new Map(FLAT.map((n) => [n.to, n.label]));

function stripTags(html: string): string {
  return html
    .replace(/<[^>]+>/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#\d+;/g, "")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

type SectionBuffer = { id: string; head: string; chunks: string[] };

export function buildPage(route: string, bodyHtml: string): IndexPage {
  const sections: SectionBuffer[] = [{ id: "", head: "Overview", chunks: [] }];
  const heading =
    /<h([123])([^>]*)>([\s\S]*?)<\/h\1>|<(pre|table)[^>]*>([\s\S]*?)<\/\4>/g;
  let match: RegExpExecArray | null;
  let tail = 0;
  while ((match = heading.exec(bodyHtml)) !== null) {
    if (match[1]) {
      const tag = match[1];
      const attrs = match[2];
      const inner = stripTags(match[3]);
      const idMatch = /id="([^"]*)"/.exec(attrs);
      sections[sections.length - 1].chunks.push(
        bodyHtml.slice(tail, match.index),
      );
      tail = heading.lastIndex;
      sections.push({
        id: tag === "1" ? "" : (idMatch ? idMatch[1] : ""),
        head: inner,
        chunks: [],
      });
    } else {
      sections[sections.length - 1].chunks.push(
        bodyHtml.slice(tail, match.index),
      );
      sections[sections.length - 1].chunks.push(match[5] ?? "");
      tail = heading.lastIndex;
    }
  }
  sections[sections.length - 1].chunks.push(bodyHtml.slice(tail));

  return {
    route,
    title: NAV_LABELS.get(route) ?? "",
    sections: sections.map((s) => ({
      id: s.id,
      head: s.head,
      text: stripTags(s.chunks.join(" ")),
    })),
  };
}

