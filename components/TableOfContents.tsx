import Link from 'next/link';

export interface TocEntry {
  id: string;
  title: string;
  level: number;
}

interface TableOfContentsProps {
  entries: TocEntry[];
}

export function TableOfContents({ entries }: TableOfContentsProps) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <aside className="hidden xl:block xl:w-48 xl:flex-shrink-0">
      <div className="sticky top-14 space-y-4 px-4 py-6 text-sm">
        <div>
          <h3 className="font-semibold mb-3 text-foreground">On this page</h3>
          <ul className="space-y-2">
            {entries.map((entry) => (
              <li key={entry.id}>
                <Link
                  href={`#${entry.id}`}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  style={{ paddingLeft: `${(entry.level - 2) * 0.75}rem` }}
                >
                  {entry.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </aside>
  );
}
