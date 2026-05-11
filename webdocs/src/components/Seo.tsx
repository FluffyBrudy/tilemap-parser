import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const SITE_NAME = "tilemap-parser";
const SITE_URL = "https://tilemap-parser.vercel.app";

const pageMeta: Record<string, { title: string; description: string }> = {
  "/": {
    title: "tilemap-parser documentation",
    description:
      "Documentation for parsing tilemap-editor map, animation, and collision JSON, then rendering tiles and moving sprites in Python games.",
  },
  "/installation": {
    title: "Install tilemap-parser",
    description:
      "Install tilemap-parser from PyPI or source to load tilemap-editor exports in a Python game project.",
  },
  "/quickstart": {
    title: "Quick start",
    description:
      "Load tilemap-editor JSON, inspect tile layers, render visible tiles, and play sprite animations with tilemap-parser.",
  },
  "/examples": {
    title: "Examples and full game demo",
    description:
      "Run focused examples or a complete pygame demo with map rendering, animation, camera movement, and collision response.",
  },
  "/api": {
    title: "API reference",
    description:
      "Reference for tilemap-parser functions, data classes, renderers, animation helpers, and collision APIs.",
  },
  "/collision": {
    title: "Collision guide",
    description:
      "Use tile collision shapes, tileset collision data, and character collision helpers in tilemap-parser.",
  },
  "/collision-runner": {
    title: "Collision runner",
    description:
      "Configure CollisionRunner for top-down and platformer movement with slide response and movement results.",
  },
  "/json-formats": {
    title: "JSON formats",
    description:
      "Tilemap-editor map, animation, tile collision, and character collision JSON format reference for tilemap-parser.",
  },
  "/technical": {
    title: "Technical docs",
    description:
      "Architecture notes for tilemap parsing, image loading, rendering caches, and collision internals.",
  },
};

function upsertMeta(selector: string, attrs: Record<string, string>) {
  let element = document.head.querySelector<HTMLMetaElement>(selector);
  if (!element) {
    element = document.createElement("meta");
    document.head.appendChild(element);
  }

  Object.entries(attrs).forEach(([key, value]) => {
    element?.setAttribute(key, value);
  });
}

function upsertCanonical(href: string) {
  let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!link) {
    link = document.createElement("link");
    link.rel = "canonical";
    document.head.appendChild(link);
  }
  link.href = href;
}

export function Seo() {
  const location = useLocation();

  useEffect(() => {
    const basePath =
      Object.keys(pageMeta)
        .filter((path) =>
          path === "/" ? location.pathname === "/" : location.pathname.startsWith(path),
        )
        .sort((a, b) => b.length - a.length)[0] ?? "/";

    const meta = pageMeta[basePath];
    const title = `${meta.title} | ${SITE_NAME}`;
    const canonical = `${SITE_URL}${location.pathname}`;

    document.title = title;
    upsertMeta('meta[name="description"]', {
      name: "description",
      content: meta.description,
    });
    upsertMeta('meta[property="og:title"]', {
      property: "og:title",
      content: title,
    });
    upsertMeta('meta[property="og:description"]', {
      property: "og:description",
      content: meta.description,
    });
    upsertMeta('meta[property="og:type"]', {
      property: "og:type",
      content: "website",
    });
    upsertMeta('meta[property="og:url"]', {
      property: "og:url",
      content: canonical,
    });
    upsertMeta('meta[name="twitter:card"]', {
      name: "twitter:card",
      content: "summary",
    });
    upsertCanonical(canonical);
  }, [location.pathname]);

  return null;
}
