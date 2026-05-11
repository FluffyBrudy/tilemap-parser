import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const capabilities = [
  {
    title: "Load editor maps",
    text: "Parse tilemap-editor JSON files and keep access to layers, tilesets, object data, and raw map metadata.",
  },
  {
    title: "Render what matters",
    text: "Use TileLayerRenderer with camera coordinates and viewport culling instead of hand-slicing tile surfaces every frame.",
  },
  {
    title: "Ship collision data",
    text: "Pair tile maps with polygon, rectangle, circle, and capsule collision shapes for top-down or platformer movement.",
  },
  {
    title: "Play sprite animations",
    text: "Load animation JSON, switch clips, and retrieve pygame surfaces from a compact AnimationPlayer API.",
  },
];

const parseTargets = [
  {
    title: "Map JSON",
    text: "Layers, z-index ordering, tile positions, tile variants, tileset references, object layers, custom properties, and raw map metadata from tilemap-editor saves.",
  },
  {
    title: "Sprite animation JSON",
    text: "Animation libraries exported by the tilemap-editor animation tool, including clip names, frame timing, playback state, and spritesheet-backed pygame surfaces.",
  },
  {
    title: "Collision JSON",
    text: "Tileset and character collision data used by CollisionCache and CollisionRunner for rectangles, circles, capsules, polygons, slopes, and movement response.",
  },
];

const docsFlow = [
  { label: "Install", to: "/installation" },
  { label: "Load a map", to: "/quickstart" },
  { label: "Run the demo", to: "/examples/full-game" },
  { label: "Check the API", to: "/api" },
];

export function Home() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl space-y-14"
    >
      <section>
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Python tools for tile-based games
        </p>
        <h1 className="max-w-4xl text-4xl font-semibold text-zinc-50 md:text-5xl">
          Load tilemap-editor exports in your pygame project.
        </h1>
        <p className="mt-5 max-w-3xl text-lg leading-8 text-zinc-400">
          tilemap-parser reads map, animation, and collision JSON produced by
          tilemap-editor, then gives you runtime helpers for layers, surfaces,
          rendering, animation playback, and collision movement.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            to="/quickstart"
            className="rounded-lg bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-zinc-950 shadow-lg shadow-cyan-500/10 hover:bg-cyan-400"
          >
            Start building
          </Link>
          <Link
            to="/examples/full-game"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-zinc-100 hover:border-zinc-600 hover:bg-zinc-800"
          >
            View full demo
          </Link>
        </div>
      </section>

      <section>
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-zinc-100">
              What the package covers
            </h2>
            <p className="mt-2 text-zinc-400">
              The docs are organized around the systems you wire together in an actual game loop.
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {capabilities.map((item) => (
            <div key={item.title} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
              <h3 className="text-base font-semibold text-zinc-100">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-6">
        <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
              Parser target
            </p>
            <h2 className="text-2xl font-semibold text-zinc-100">
              Built for tilemap-editor output
            </h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">
              tilemap-parser is the runtime-side package for projects built
              with tilemap-editor. The editor is the pygame tool for creating
              maps and sprite animations; this package loads those exported
              JSON files in your game code.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a
                href="https://pypi.org/project/tilemap-editor/"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 hover:border-cyan-700/60 hover:bg-zinc-900"
              >
                tilemap-editor on PyPI
              </a>
              <a
                href="https://github.com/FluffyBrudy/tilemap-editor"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 hover:border-cyan-700/60 hover:bg-zinc-900"
              >
                tilemap-editor on GitHub
              </a>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-1">
            {parseTargets.map((item) => (
              <div key={item.title} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
                <h3 className="text-sm font-semibold text-zinc-100">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-zinc-400">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-6">
        <h2 className="text-xl font-semibold text-zinc-100">Recommended path</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {docsFlow.map((step, index) => (
            <Link
              key={step.to}
              to={step.to}
              className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-4 hover:border-cyan-700/60 hover:bg-zinc-800"
            >
              <span className="text-xs font-medium text-cyan-300">
                Step {index + 1}
              </span>
              <span className="mt-2 block text-sm font-semibold text-zinc-100">
                {step.label}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </motion.div>
  );
}
