import { Link, useLocation } from "react-router-dom";
import { FLAT } from "../nav";

export default function FooterNav() {
  const { pathname } = useLocation();
  const i = FLAT.findIndex((n) => n.to === pathname);
  if (i === -1) return null;
  const prev = FLAT[i - 1];
  const next = FLAT[i + 1];
  return (
    <footer className="mt-20 grid gap-4 border-t-2 border-line-2 pt-8 sm:grid-cols-2">
      {prev ? (
        <Link to={prev.to} className="btn-pixel text-left" data-accent="amber">
          <span className="block font-pixel text-[8px] text-mute">◂ PREV</span>
          {prev.label}
        </Link>
      ) : (
        <span />
      )}
      {next ? (
        <Link to={next.to} className="btn-pixel text-right">
          <span className="block font-pixel text-[8px] text-mute">NEXT ▸</span>
          {next.label}
        </Link>
      ) : (
        <span />
      )}
    </footer>
  );
}
