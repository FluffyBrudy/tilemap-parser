import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { FLAT, NAV, REPO, VERSION } from "../nav";
import { PixelMark } from "./PixelSprite";
import FooterNav from "./FooterNav";

export default function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);
  const current = FLAT.find((n) => n.to === pathname);

  return (
    <div className="min-h-screen bg-ink text-text">
      <header className="fixed inset-x-0 top-0 z-40 h-14 border-b-2 border-line-2 bg-panel">
        <div className="flex h-full items-center gap-3 px-4">
          <button
            onClick={() => setOpen((v) => !v)}
            className="btn-pixel lg:hidden"
            aria-label="Toggle navigation"
          >
            {open ? "CLOSE" : "MENU"}
          </button>
          <Link
            to="/"
            className="flex items-center gap-2 hover:bg-teal hover:text-ink"
          >
            <PixelMark className="h-6 w-6" />
            <span className="font-pixel text-[11px]">tilemap-parser</span>
          </Link>
          <span className="border-2 border-line-2 bg-raise px-2 py-0.5 font-pixel text-[8px] text-amber">
            v{VERSION}
          </span>
          <span className="hidden flex-1 text-right font-retro text-[22px] leading-none text-mute md:block">
            {current ? current.label : "collision for game devs"}
          </span>
          <a href={REPO} className="btn-pixel">
            GITHUB
          </a>
        </div>
      </header>

      <aside
        className={`fixed bottom-0 left-0 top-14 z-30 w-64 overflow-y-auto border-r-2 border-line-2 bg-panel transition-transform lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <nav className="p-3">
          {NAV.map((group) => (
            <div key={group.title} className="mb-6">
              <div className="mb-2 border-b-2 border-line px-2 pb-1 font-pixel text-[8px] text-mute">
                {group.title}
              </div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `mb-1 flex items-center gap-2 border-2 px-3 py-2 font-mono text-[13px] ${
                      isActive
                        ? "border-teal bg-teal font-bold text-ink"
                        : "border-transparent text-mute hover:border-line-2 hover:bg-panel-2 hover:text-text"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span aria-hidden="true" className="w-2 text-[10px]">
                        {isActive ? "▶" : "·"}
                      </span>
                      {item.label}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <main className="lg:pl-64">
        <div className="mx-auto max-w-[860px] px-5 pb-16 pt-24 sm:px-8">
          {children}
          <FooterNav />
        </div>
      </main>
    </div>
  );
}
