import { motion } from "framer-motion";
import { useParams, useNavigate } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";
import demoSrc from "../../../examples/demo/main.py?raw";

const examples = [
  {
    id: "demo",
    title: "All features demo",
    description:
      "A single-file pygame-ce demo that showcases tile map parsing, tile rendering, tile-vs-player collision, object-to-object collision with mixed shapes, and sprite animation — no external assets needed.",
    difficulty: "Intermediate",
    projectPath: "examples/demo",
    runCommand: "python main.py",
    highlights: [
      "Inline map data parsed via parse_map_dict() — no JSON files required",
      "Inline tileset collision via parse_tileset_collision()",
      "Tile rendering with TileLayerRenderer and viewport culling",
      "Tile-vs-player collision with CollisionRunner.move_and_slide()",
      "Object-to-object collision with circle, capsule, and rectangle shapes",
      "Sprite animation with AnimationPlayer and programmatic spritesheet",
      "pygame-ce shape drawing for collision debug visualization",
      "Camera follow, collision tile highlights, and HUD overlay",
    ],
    features: [
      "Inline data construction",
      "Tile rendering and collision",
      "Object-to-object collision",
      "Animation playback",
      "Camera-follow movement",
      "Debug collision visualization",
      "Single-file, zero external assets",
    ],
    code: demoSrc,
    downloadUrl: "/examples/demo.zip",
    sourceUrl:
      "https://github.com/FluffyBrudy/tilemap-parser/tree/main/examples/demo",
  },
];

export function Examples() {
  const { exampleId } = useParams();
  const navigate = useNavigate();
  const selectedExample = examples.find((ex) => ex.id === exampleId);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Beginner":
        return "text-green-400 bg-green-400/10 border-green-400/20";
      case "Intermediate":
        return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
      case "Advanced":
        return "text-red-400 bg-red-400/10 border-red-400/20";
      default:
        return "text-zinc-400 bg-zinc-400/10 border-zinc-400/20";
    }
  };

  if (selectedExample) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-5xl"
      >
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
          <button
            onClick={() => navigate("/examples")}
            className="hover:text-zinc-300 transition-colors"
          >
            Examples
          </button>
          <span>/</span>
          <span className="text-zinc-300">{selectedExample.title}</span>
        </div>

        <div className="mb-8">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-zinc-100">
              {selectedExample.title}
            </h1>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-medium ${getDifficultyColor(selectedExample.difficulty)}`}
            >
              {selectedExample.difficulty}
            </span>
          </div>
          <p className="max-w-3xl text-lg leading-8 text-zinc-400">
            {selectedExample.description}
          </p>
        </div>

        <div className="mb-8 grid gap-4 rounded-lg border border-zinc-800 bg-zinc-950 p-5 md:grid-cols-3">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Project
            </div>
            <div className="mt-2 font-mono text-sm text-zinc-200">
              {selectedExample.projectPath}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Run
            </div>
            <div className="mt-2 font-mono text-sm text-zinc-200">
              {selectedExample.runCommand}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Includes
            </div>
            <div className="mt-2 text-sm text-zinc-300">
              Single Python file, no external assets
            </div>
          </div>
        </div>

        <div className="mb-8 flex flex-wrap gap-3">
          <a
            href={selectedExample.downloadUrl}
            className="flex items-center gap-2 rounded-lg bg-cyan-500 px-5 py-2.5 font-medium text-zinc-950 shadow-lg shadow-cyan-500/10 transition-colors hover:bg-cyan-400"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Download Example
          </a>
          <a
            href={selectedExample.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-5 py-2.5 font-medium text-zinc-100 transition-colors hover:bg-zinc-700"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            View on GitHub
          </a>
        </div>

        <div className="mb-8 rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
          <h2 className="mb-4 text-xl font-semibold text-zinc-100">
            What this demonstrates
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {selectedExample.highlights.map((feature, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <svg
                  className="mt-0.5 h-5 w-5 flex-shrink-0 text-cyan-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span className="text-zinc-300">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-zinc-100">
            Code preview
          </h2>
          <CodeBlock code={selectedExample.code} title="examples/demo/main.py" />
        </div>

        <div className="flex justify-between items-center pt-8 border-t border-zinc-800">
          <button
            onClick={() => navigate("/examples")}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Examples
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl"
    >
      <section className="mb-12">
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Learn by running code
        </p>
        <h1 className="mb-4 text-4xl font-semibold text-zinc-100">Examples</h1>
        <p className="max-w-3xl text-lg leading-8 text-zinc-400">
          A single-file demo you can download and run. All data is inlined — no
          external JSON, images, or config files needed. Just
          install and run.
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {examples.map((example, idx) => (
          <motion.div
            key={example.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => navigate(`/examples/${example.id}`)}
            className="group cursor-pointer rounded-lg border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-cyan-700/60 hover:bg-zinc-900"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-semibold text-zinc-100 transition-colors group-hover:text-cyan-300">
                {example.title}
              </h3>
              <span
                className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getDifficultyColor(example.difficulty)}`}
              >
                {example.difficulty}
              </span>
            </div>

            <p className="text-zinc-400 text-sm mb-4 line-clamp-3">
              {example.description}
            </p>

            <div className="mb-6 space-y-2">
              {example.features.slice(0, 3).map((feature, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-sm text-zinc-500"
                >
                  <svg
                    className="w-4 h-4 text-zinc-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>{feature}</span>
                </div>
              ))}
              {example.features.length > 3 && (
                <div className="text-xs text-zinc-600 ml-6">
                  +{example.features.length - 3} more features
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 text-sm font-medium text-cyan-300 group-hover:text-cyan-200">
              <span>View Example</span>
              <svg
                className="w-4 h-4 group-hover:translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </motion.div>
        ))}
      </div>

      <section className="mt-16 rounded-lg border border-zinc-800 bg-zinc-950 p-8">
        <h2 className="mb-4 text-2xl font-semibold text-zinc-100">
          Run locally
        </h2>
        <div className="space-y-4 text-zinc-300">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              1
            </div>
            <div>
              <h3 className="font-medium mb-1">Get the file</h3>
              <p className="text-sm text-zinc-400">
                Download the zip above, or copy the code from the detail page.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              2
            </div>
            <div>
              <h3 className="font-medium mb-1">Install Dependencies</h3>
              <p className="text-sm text-zinc-400">
                Run{" "}
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">
                  pip install tilemap-parser pygame-ce
                </code>{" "}
                in your terminal.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              3
            </div>
            <div>
              <h3 className="font-medium mb-1">Run it</h3>
              <p className="text-sm text-zinc-400">
                Extract <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">demo.zip</code> and run
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300"> python main.py</code>.
              </p>
            </div>
          </div>
        </div>
      </section>
    </motion.div>
  );
}
