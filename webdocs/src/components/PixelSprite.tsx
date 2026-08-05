export function PixelMark({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      className={className}
      shapeRendering="crispEdges"
      aria-hidden="true"
    >
      <rect width="16" height="16" fill="#14111d" />
      <rect x="2" y="2" width="3" height="3" fill="#3ee6c4" />
      <rect x="6" y="2" width="3" height="3" fill="#ff5d5d" />
      <rect x="10" y="2" width="4" height="3" fill="#7aa2ff" />
      <rect x="2" y="6" width="3" height="4" fill="#ffc857" />
      <rect x="6" y="6" width="3" height="4" fill="#3ee6c4" />
      <rect x="10" y="6" width="4" height="4" fill="#b48cff" />
      <rect x="2" y="11" width="12" height="3" fill="#322a49" />
    </svg>
  );
}
export function HeroSprite({ className = "w-80" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 96 64"
      className={className}
      shapeRendering="crispEdges"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <rect width="96" height="64" fill="#0d0b13" />

      <rect x="8" y="8" width="2" height="2" fill="#3a3157" />
      <rect x="24" y="14" width="2" height="2" fill="#3a3157" />
      <rect x="74" y="10" width="2" height="2" fill="#3a3157" />

      <rect x="0" y="36" width="96" height="2" fill="#19152a" />

      <rect x="0" y="38" width="96" height="26" fill="#2b243d" />
      <rect x="0" y="38" width="96" height="2" fill="#433760" />

      {Array.from({ length: 6 }).map((_, i) => (
        <rect key={i} x={i * 16} y={38} width="8" height="26" fill="#241d34" />
      ))}

      <rect x="72" y="18" width="16" height="20" fill="#50466f" />
      <rect x="72" y="18" width="16" height="2" fill="#6c5f96" />

      <rect x="52" y="22" width="14" height="14" fill="#ffc857" />
      <rect x="52" y="22" width="14" height="2" fill="#ffe38d" />
      <rect x="58" y="22" width="2" height="14" fill="#c58a1d" />
      <rect x="52" y="28" width="14" height="2" fill="#c58a1d" />

      <rect x="40" y="27" width="8" height="2" fill="#ff5d5d" />
      <rect x="46" y="25" width="4" height="6" fill="#ff5d5d" />

      <g className="animate-bob">
        <rect x="14" y="36" width="16" height="2" fill="#0b0911" />

        <rect x="16" y="20" width="12" height="16" fill="#7aa2ff" />
        <rect x="16" y="20" width="12" height="2" fill="#a9c2ff" />

        <rect x="19" y="26" width="1" height="1" fill="#111" />
        <rect x="24" y="26" width="1" height="1" fill="#111" />

        <rect x="21" y="30" width="2" height="1" fill="#111" />

        <rect x="17" y="34" width="3" height="2" fill="#5f82d8" />
        <rect x="24" y="34" width="3" height="2" fill="#5f82d8" />
      </g>
    </svg>
  );
}
