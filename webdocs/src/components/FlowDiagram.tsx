import { Link } from "react-router-dom";

export type FlowNode = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  lines?: string[];
  accent?: "red" | "amber" | "teal" | "blue" | "purple";
  link?: string;
};

export type FlowEdge = {
  from: string;
  to: string;
  label?: string;
  fromSide?: Side;
  fromOffset?: number;
  toSide?: Side;
  toOffset?: number;
  elbow?: number;
  color?: "red" | "amber" | "teal" | "blue" | "purple";
};

type Side = "bottom" | "right" | "top" | "left";

type Props = {
  title?: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
};

const ACCENT: Record<string, string> = {
  red: "var(--red)",
  amber: "var(--amber)",
  teal: "var(--teal)",
  blue: "var(--blue)",
  purple: "var(--purple)",
};

const PAD = 16;

type Route = {
  points: string;
  arrow: string;
  labelX: number;
  labelY: number;
  labelAnchor: "start" | "middle" | "end";
};

function anchor(n: FlowNode, side: Side, offset: number): [number, number] {
  switch (side) {
    case "bottom":
      return [n.x + n.w * offset, n.y + n.h];
    case "top":
      return [n.x + n.w * offset, n.y];
    case "left":
      return [n.x, n.y + n.h * offset];
    default:
      return [n.x + n.w, n.y + n.h * offset];
  }
}

function routeEdge(from: FlowNode, to: FlowNode, e: FlowEdge): Route {
  const fs = e.fromSide ?? "bottom";
  const ts = e.toSide ?? "top";
  const [ax, ay] = anchor(from, fs, e.fromOffset ?? 0.5);
  const [bx, by] = anchor(to, ts, e.toOffset ?? 0.5);

  const vfs = fs === "bottom" || fs === "top";
  const vts = ts === "bottom" || ts === "top";

  let pts: [number, number][];
  let labelX = 0;
  let labelY = 0;
  let labelAnchor: "start" | "middle" | "end" = "middle";

  if (vfs && vts) {
    const midY = e.elbow ?? (ay + by) / 2;
    pts = [
      [ax, ay],
      [ax, midY],
      [bx, midY],
      [bx, by],
    ];
    labelX = ax + 10;
    labelY = midY + 6;
    labelAnchor = "start";
  } else if (!vfs && !vts) {
    const midX = e.elbow ?? (ax + bx) / 2;
    pts = [
      [ax, ay],
      [midX, ay],
      [midX, by],
      [bx, by],
    ];
    labelX = midX + 10;
    labelY = (ay + by) / 2 + 6;
    labelAnchor = "start";
  } else if (vfs) {
    pts = [
      [ax, ay],
      [ax, by],
      [bx, by],
    ];
    labelX = (ax + bx) / 2;
    labelY = by - 10;
  } else {
    pts = [
      [ax, ay],
      [bx, ay],
      [bx, by],
    ];
    labelX = bx + 10;
    labelY = (ay + by) / 2 + 6;
    labelAnchor = "start";
  }

  const points = pts.map(([x, y]) => `${x},${y}`).join(" ");
  const arrow =
    ts === "top"
      ? `${bx - 4},${by - 8} ${bx + 4},${by - 8} ${bx},${by}`
      : `${bx - 8},${by - 4} ${bx - 8},${by + 4} ${bx},${by}`;

  return { points, arrow, labelX, labelY, labelAnchor };
}

export default function FlowDiagram({ title = "data flow", nodes, edges }: Props) {
  const width = Math.max(...nodes.map((n) => n.x + n.w)) + PAD;
  const height = Math.max(...nodes.map((n) => n.y + n.h)) + PAD;
  const byId = new Map(nodes.map((n) => [n.id, n]));

  return (
    <figure className="my-6 overflow-x-auto border-2 border-line-2 bg-[#0a0810] shadow-hard">
      <figcaption className="flex items-center gap-3 border-b-2 border-line-2 bg-panel-2 px-3 py-2">
        <span className="h-3 w-3 border border-line-2 bg-red" aria-hidden="true" />
        <span className="h-3 w-3 border border-line-2 bg-amber" aria-hidden="true" />
        <span className="h-3 w-3 border border-line-2 bg-teal" aria-hidden="true" />
        <span className="flex-1 truncate font-mono text-[12px] text-mute">
          {title}
        </span>
        <span className="font-pixel text-[8px] text-mute">DIAGRAM</span>
      </figcaption>

      <div className="relative" style={{ width, height }}>
        <svg
          width={width}
          height={height}
          className="absolute inset-0"
          style={{ overflow: "visible" }}
          aria-hidden="true"
        >
          {edges.map((e, i) => {
            const from = byId.get(e.from);
            const to = byId.get(e.to);
            if (!from || !to) return null;
            const r = routeEdge(from, to, e);
            const color = e.color ? ACCENT[e.color] : "var(--teal)";
            return (
              <g key={`${i}:${e.from}->${e.to}`}>
                <polyline
                  className="flow-edge"
                  points={r.points}
                  style={{ stroke: color }}
                />
                <polygon className="flow-arrow" points={r.arrow} style={{ fill: color }} />
                {e.label && (
                  <text
                    className="flow-label"
                    x={r.labelX}
                    y={r.labelY}
                    textAnchor={r.labelAnchor}
                  >
                    {e.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {nodes.map((n) => {
          const inner = (
            <>
              <div className="flow-node-title">
                <span
                  className="flow-node-cursor"
                  style={{ background: n.accent ? ACCENT[n.accent] : "var(--teal)" }}
                />
                {n.title}
              </div>
              <div className="flow-node-body">
                {n.lines?.map((l) => (
                  <div key={l}>{l}</div>
                ))}
              </div>
            </>
          );
          const style = {
            left: n.x,
            top: n.y,
            width: n.w,
            height: n.h,
          } as const;
          return n.link ? (
            n.link.startsWith("#") ? (
              <a key={n.id} className="flow-node" href={n.link} style={style}>
                {inner}
              </a>
            ) : (
              <Link key={n.id} className="flow-node" to={n.link} style={style}>
                {inner}
              </Link>
            )
          ) : (
            <div key={n.id} className="flow-node" style={style}>
              {inner}
            </div>
          );
        })}
      </div>
    </figure>
  );
}
