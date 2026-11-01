import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

type IndexSection = { id: string; head: string; text: string };
type IndexPage = { route: string; title: string; sections: IndexSection[] };
type Hit = { route: string; title: string; id: string; head: string; score: number; snippet: string };

let indexPromise: Promise<IndexPage[]> | null = null;
let indexCache: IndexPage[] | null = null;

function loadIndex(): Promise<IndexPage[]> {
  if (indexCache !== null) {
    return Promise.resolve(indexCache);
  }
  if (indexPromise === null) {
    indexPromise = fetch("/search-index.json")
      .then(async (r) => {
        if (!r.ok) throw new Error(`search index unavailable (${r.status})`);
        const contentType = r.headers.get("content-type") ?? "";
        if (!contentType.includes("json")) {
          throw new Error("search index unavailable");
        }
        return (await r.json()) as IndexPage[];
      })
      .then((pages) => {
        if (pages.length === 0) {
          indexPromise = null;
          throw new Error("search index is empty");
        }
        indexCache = pages;
        return pages;
      })
      .catch((error: unknown) => {
        indexPromise = null;
        indexCache = null;
        throw error;
      });
  }
  return indexPromise;
}

function snippetAround(text: string, term: string): string {
  const at = text.toLowerCase().indexOf(term);
  if (at < 0) return text.slice(0, 90);
  const start = Math.max(0, at - 30);
  const raw = text.slice(start, start + 110);
  return (start > 0 ? "…" : "") + raw.trim() + (start + 110 < text.length ? "…" : "");
}

function scoreIndex(query: string, pages: IndexPage[]): Hit[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length === 0) return [];
  const hits: Hit[] = [];
  for (const page of pages) {
    const pageTitle = page.title.toLowerCase();
    for (const section of page.sections) {
      const head = section.head.toLowerCase();
      const text = section.text.toLowerCase();
      let score = 0;
      for (const term of terms) {
        if (term.length === 0) continue;
        if (head.includes(term)) score += 40;
        else if (head.startsWith(term[0]) && head.split(" ")[0].startsWith(term)) score += 24;
        else if (pageTitle.includes(term)) score += 20;
        else if (text.includes(term)) score += 10;
        else {
          score = 0;
          break;
        }
      }
      if (score <= 0) continue;
      hits.push({
        route: page.route,
        title: page.title,
        id: section.id,
        head: section.head,
        score,
        snippet: snippetAround(section.text, terms[terms.length - 1]),
      });
    }
  }
  return hits.sort((a, b) => b.score - a.score).slice(0, 24);
}

export default function SearchModal() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [pages, setPages] = useState<IndexPage[] | null>(() => indexCache);
  const [state, setState] = useState<"loading" | "ready" | "failed">(() =>
    indexCache ? "ready" : "loading",
  );
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setActive(0);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA";
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      } else if (!typing && e.key === "/" && !open) {
        e.preventDefault();
        setOpen(true);
      } else if (e.key === "Escape" && open) {
        close();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  useEffect(() => {
    if (!open || pages !== null) return;
    let cancelled = false;
    setState("loading");
    loadIndex()
      .then((loaded) => {
        if (cancelled) return;
        setPages(loaded);
        setState("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setState("failed");
      });
    return () => {
      cancelled = true;
    };
  }, [open, pages]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const hits = useMemo(() => {
    if (!pages || !query.trim()) return [];
    return scoreIndex(query, pages);
  }, [pages, query]);

  const navigateTo = (hit: Hit) => {
    navigate(hit.id ? `${hit.route}#${hit.id}` : hit.route);
    close();
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="btn-pixel hidden font-mono text-[12px] sm:block"
        aria-label="Open search"
        title="Search (Ctrl+K)"
      >
        SEARCH
      </button>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 px-4 pt-24"
      onMouseDown={close}
    >
      <div
        className="w-full max-w-[560px] border-2 border-line-2 bg-panel shadow-hard"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b-2 border-line-2 bg-raise px-3 py-2">
          <span className="font-pixel text-[9px] text-teal">SEARCH</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive((v) => Math.min(v + 1, Math.max(0, hits.length - 1)));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive((v) => Math.max(v - 1, 0));
              } else if (e.key === "Enter" && hits[active]) {
                navigateTo(hits[active]);
              }
            }}
            placeholder="docs query…"
            className="flex-1 bg-transparent font-mono text-[14px] text-text outline-none placeholder:text-mute"
            autoFocus
          />
          <kbd
            onClick={close}
            className="cursor-pointer border-2 border-line-2 px-1 font-pixel text-[8px] text-mute hover:border-teal hover:text-text"
            title="Close (ESC)"
          >
            ESC
          </kbd>
        </div>
        <div className="max-h-[380px] overflow-y-auto">
          {state !== "ready" ? (
            <p className="px-3 py-4 font-mono text-[13px] text-mute">
              {state === "failed"
                ? "search index unavailable — run npm run build, or reload in dev"
                : "loading index…"}
            </p>
          ) : hits.length === 0 ? (
            <p className="px-3 py-4 font-mono text-[13px] text-mute">
              {query ? "no matches" : "type to search all pages"}
            </p>
          ) : (
            hits.map((hit, i) => (
              <button
                key={`${hit.route}#${hit.id}#${i}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => navigateTo(hit)}
                className={`block w-full border-b-2 border-line px-3 py-2 text-left font-mono text-[13px] ${
                  i === active
                    ? "bg-teal text-ink"
                    : "text-text hover:bg-panel-2"
                }`}
              >
                <span className="block font-pixel text-[8px] text-mute">
                  {hit.title}
                </span>
                <span className="block text-teal">
                  {hit.head || "Overview"}
                </span>
                <span
                  className={`block truncate text-[12px] ${
                    i === active ? "text-ink/80" : "text-mute"
                  }`}
                >
                  {hit.snippet}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
