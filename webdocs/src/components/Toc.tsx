export type TocItem = { id: string; label: string };

export default function Toc({ items }: { items: TocItem[] }) {
  return (
    <aside className="panel-flat my-6 p-4">
      <div className="font-pixel mb-3 text-[9px] text-amber">ON THIS PAGE</div>
      <ul className="list-none">
        {items.map((it) => (
          <li key={it.id} className="my-1">
            <a
              href={`#${it.id}`}
              className="block border-b-0 py-1 font-mono text-[13px] text-mute hover:bg-teal hover:text-ink"
            >
              <span className="mr-2 text-teal">▪</span>
              {it.label}
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
