import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";

export function Installation() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl"
    >
      <h2 className="text-2xl font-semibold text-zinc-100 mb-4">Installation</h2>
      <p className="text-zinc-400 mb-6">
        Install tilemap-parser from PyPI or directly from source.
      </p>

      <h3 className="text-lg font-medium text-zinc-200 mb-3">pip</h3>
      <CodeBlock code="pip install tilemap-parser" />

      <h3 className="text-lg font-medium text-zinc-200 mb-3 mt-8">Development</h3>
      <CodeBlock code={`# Clone the repository
git clone https://github.com/your-org/tilemap-parser.git
cd tilemap-parser

# Install in editable mode
pip install -e .`} />

      <h3 className="text-lg font-medium text-zinc-200 mb-3 mt-8">Dependencies</h3>
      <p className="text-zinc-400 mb-2">Requires Python 3.10+ and pygame-ce:</p>
      <CodeBlock code="pip install pygame-ce>=2.5" />
    </motion.div>
  );
}