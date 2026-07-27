'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { navigation } from '@/lib/navigation';

export function Sidebar() {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState<string[]>([]);

  const isActive = (href?: string) => href && pathname.startsWith(href);

  const toggleSection = (title: string) => {
    setExpanded((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  return (
    <aside className="hidden lg:flex lg:w-64 lg:border-r lg:border-border lg:flex-col">
      <nav className="flex-1 overflow-y-auto px-3 py-6">
        <ul className="space-y-2">
          {navigation.map((section) => (
            <li key={section.title}>
              <button
                onClick={() => toggleSection(section.title)}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
              >
                {section.title}
                {section.items && (
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      expanded.includes(section.title) ? 'rotate-180' : ''
                    }`}
                  />
                )}
              </button>

              {section.items && expanded.includes(section.title) && (
                <ul className="ml-2 mt-1 space-y-1 border-l border-border pl-3">
                  {section.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href || '#'}
                        className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                          isActive(item.href)
                            ? 'bg-accent text-accent-foreground font-semibold'
                            : 'hover:bg-muted'
                        }`}
                      >
                        {item.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
