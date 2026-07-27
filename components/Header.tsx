'use client';

import Link from 'next/link';
import { useTheme } from 'next-themes';
import { Moon, Sun, Github, Search } from 'lucide-react';
import { useEffect, useState } from 'react';

export function Header() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <span>Tilemap Parser</span>
        </Link>

        <nav className="flex items-center gap-4">
          <button
            aria-label="Search"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-muted"
            onClick={() => {
              // Search will be implemented with Pagefind
            }}
          >
            <Search className="h-5 w-5" />
          </button>

          <a
            href="https://github.com/FluffyBrudy/tilemap-parser"
            aria-label="GitHub"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-muted"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Github className="h-5 w-5" />
          </a>

          {mounted && (
            <button
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-muted"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
