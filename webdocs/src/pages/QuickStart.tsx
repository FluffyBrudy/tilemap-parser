import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";
import demoSrc from "../../../examples/demo/main.py?raw";

export function QuickStart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl"
    >
      <section className="mb-8">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-4">Quick Start</h2>
        <p className="text-zinc-400 mb-4 max-w-3xl leading-relaxed">
          This single-file demo uses every major feature of{" "}
          <code className="text-cyan-300">tilemap-parser</code> — tile map
          parsing, tile rendering with viewport culling, tile-vs-player collision,
          object-to-object collision (circle, capsule, rect), and sprite animation.
          All data is inlined so it runs with just{" "}
          <code className="px-1.5 py-0.5 rounded bg-zinc-800 text-cyan-200 text-sm">
            pip install tilemap-parser pygame-ce
          </code>
          .
        </p>
        <p className="text-zinc-500 text-sm mb-6">
          You can also{" "}
          <a href="/examples" className="text-cyan-400 hover:text-cyan-300 underline">
            browse the examples page
          </a>{" "}
          to download the source as a zip.
        </p>
      </section>

      <CodeBlock code={demoSrc} title="examples/demo/main.py" />
    </motion.div>
  );
}
