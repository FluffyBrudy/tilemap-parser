import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { StaticRouter } from "react-router-dom";
import App from "../src/App";
import { SEO, SITE_DESCRIPTION, SITE_URL, SITEMAP_ROUTES } from "../src/seo";

const OUT = path.resolve(process.cwd(), "dist");
const TEMPLATE = readFileSync(path.join(OUT, "index.html"), "utf8");

function pageUrl(route: string): string {
  return route === "/" ? SITE_URL : `${SITE_URL}${route}/`;
}

function renderBody(route: string): string {
  const app = createElement(
    StaticRouter,
    { location: route },
    createElement(App),
  );
  return renderToString(app);
}

function renderPage(route: string): string {
  const seo = SEO[route] ?? { title: "tilemap-parser — docs", description: SITE_DESCRIPTION };
  const url = pageUrl(route);
  let html = TEMPLATE.replace(
    '<div id="root"></div>',
    `<div id="root">${renderBody(route)}</div>`,
  );
  html = html.replace(/<title>[^<]*<\/title>/, `<title>${seo.title}</title>`);
  html = html.replace(
    /<meta name="description" content="[^"]*"/,
    `<meta name="description" content="${seo.description}"`,
  );
  html = html.replace(
    /<meta property="og:title" content="[^"]*"/,
    `<meta property="og:title" content="${seo.title}"`,
  );
  html = html.replace(
    /<meta\s*property="og:description"[\s\S]*?content="[^"]*"/,
    `<meta property="og:description" content="${seo.description}"`,
  );
  html = html.replace(
    /<meta property="og:url" content="[^"]*"/,
    `<meta property="og:url" content="${url}"`,
  );
  html = html.replace(
    /<meta name="twitter:title" content="[^"]*"/,
    `<meta name="twitter:title" content="${seo.title}"`,
  );
  html = html.replace(
    /<meta\s*name="twitter:description"[\s\S]*?content="[^"]*"/,
    `<meta name="twitter:description" content="${seo.description}"`,
  );
  html = html.replace(
    "</head>",
    `<link rel="canonical" href="${url}" />\n  </head>`,
  );
  return html;
}

function sitemapXml(): string {
  const urls = SITEMAP_ROUTES.map((r) => {
    return `  <url><loc>${pageUrl(r.path)}</loc><changefreq>monthly</changefreq><priority>${r.priority}</priority></url>`;
  }).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
}

for (const route of SITEMAP_ROUTES.map((r) => r.path)) {
  const dest =
    route === "/"
      ? path.join(OUT, "index.html")
      : path.join(OUT, route, "index.html");
  mkdirSync(path.dirname(dest), { recursive: true });
  writeFileSync(dest, renderPage(route));
  process.stdout.write(`prerendered ${route}\n`);
}
writeFileSync(path.join(OUT, "sitemap.xml"), sitemapXml());
process.stdout.write("sitemap.xml written\n");