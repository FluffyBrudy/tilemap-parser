import type { ReactNode } from "react";

const KINDS = {
  info: {
    border: "border-l-blue",
    text: "text-blue",
    label: "INFO",
  },
  note: {
    border: "border-l-blue",
    text: "text-blue",
    label: "NOTE",
  },
  warn: {
    border: "border-l-amber",
    text: "text-amber",
    label: "WATCH OUT",
  },
  danger: {
    border: "border-l-red",
    text: "text-red",
    label: "TRAP",
  },
  tip: {
    border: "border-l-teal",
    text: "text-teal",
    label: "WHY",
  },
} as const;

export default function Callout({
  kind = "note",
  title,
  id,
  children,
}: {
  kind?: Kind;
  title?: string;
  id?: string;
  children: ReactNode;
}) {
  const k = KINDS[kind];
  return (
    <aside
      id={id}
      className={`my-6 border-2 border-line-2 border-l-8 ${k.border} bg-panel p-4 shadow-hard-sm`}
    >
      <div className={`font-pixel mb-2 text-[9px] ${k.text}`}>
        {title ?? k.label}
      </div>
      <div className="text-text">{children}</div>
    </aside>
  );
}

type Kind = keyof typeof KINDS;
