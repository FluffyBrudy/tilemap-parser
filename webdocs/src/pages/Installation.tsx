import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";

export function Installation() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl"
    >
      {/* Hero Section */}
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-zinc-100 mb-4">
          Get Started with tilemap-parser
        </h1>
        <p className="text-lg text-zinc-400">
          Install tilemap-parser and start building 2D games with powerful
          tilemap and collision features.
        </p>
      </div>

      {/* Quick Install */}
      <section className="mb-12">
        <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-800/30 rounded-xl p-8">
          <h2 className="text-2xl font-semibold text-zinc-100 mb-4">
            Quick Install
          </h2>
          <p className="text-zinc-300 mb-4">Install via pip (recommended):</p>
          <CodeBlock
            code="pip install tilemap-parser"
            language="bash"
            title="Terminal"
          />
        </div>
      </section>

      {/* Requirements */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-6">
          Requirements
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-zinc-200">Python</h3>
            </div>
            <p className="text-zinc-400 text-sm">
              Python 3.10 or higher is required
            </p>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-zinc-200">pygame-ce</h3>
            </div>
            <p className="text-zinc-400 text-sm">pygame-ce 2.5.0 or higher</p>
          </div>
        </div>
      </section>

      {/* Installation Methods */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-6">
          Installation Methods
        </h2>

        <div className="space-y-6">
          {/* PyPI */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="text-xl font-medium text-zinc-200">From PyPI</h3>
              <span className="px-2 py-0.5 text-xs font-medium bg-green-400/10 text-green-400 border border-green-400/20 rounded-full">
                Recommended
              </span>
            </div>
            <p className="text-zinc-400 mb-4">
              The easiest way to install tilemap-parser is from the Python
              Package Index:
            </p>
            <CodeBlock code="pip install tilemap-parser" language="bash" />
          </div>

          {/* With Dependencies */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-xl font-medium text-zinc-200 mb-4">
              With All Dependencies
            </h3>
            <p className="text-zinc-400 mb-4">
              Install tilemap-parser along with pygame-ce in one command:
            </p>
            <CodeBlock
              code="pip install tilemap-parser pygame-ce>=2.5"
              language="bash"
            />
          </div>

          {/* Development */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-xl font-medium text-zinc-200 mb-4">
              Development Installation
            </h3>
            <p className="text-zinc-400 mb-4">
              For contributing or development, install from source:
            </p>
            <CodeBlock
              code={`# Clone the repository
git clone https://github.com/FluffyBrudy/tilemap-parser.git
cd tilemap-parser

# Install in editable mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"`}
              language="bash"
            />
          </div>
        </div>
      </section>

      {/* Verify Installation */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-6">
          Verify Installation
        </h2>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
          <p className="text-zinc-400 mb-4">
            Test your installation by importing the package:
          </p>
          <CodeBlock
            code={`import tilemap_parser

# Check version
print(tilemap_parser.__version__)

# Try importing main components
from tilemap_parser import load_map, SpriteAnimationSet, CollisionRunner
print("✓ Installation successful!")`}
            language="python"
            title="test_install.py"
          />
        </div>
      </section>

      {/* Next Steps */}
      <section className="bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-6">
          Next Steps
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          <a
            href="/quickstart"
            className="group bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 hover:border-zinc-600 rounded-lg p-4 transition-all"
          >
            <div className="flex items-center gap-2 mb-2">
              <svg
                className="w-5 h-5 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <h3 className="font-medium text-zinc-200 group-hover:text-blue-400 transition-colors">
                Quick Start
              </h3>
            </div>
            <p className="text-sm text-zinc-500">
              Learn the basics in 5 minutes
            </p>
          </a>

          <a
            href="/examples"
            className="group bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 hover:border-zinc-600 rounded-lg p-4 transition-all"
          >
            <div className="flex items-center gap-2 mb-2">
              <svg
                className="w-5 h-5 text-purple-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
              <h3 className="font-medium text-zinc-200 group-hover:text-purple-400 transition-colors">
                Examples
              </h3>
            </div>
            <p className="text-sm text-zinc-500">
              Explore complete code examples
            </p>
          </a>

          <a
            href="/api"
            className="group bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 hover:border-zinc-600 rounded-lg p-4 transition-all"
          >
            <div className="flex items-center gap-2 mb-2">
              <svg
                className="w-5 h-5 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                />
              </svg>
              <h3 className="font-medium text-zinc-200 group-hover:text-green-400 transition-colors">
                API Reference
              </h3>
            </div>
            <p className="text-sm text-zinc-500">Detailed API documentation</p>
          </a>
        </div>
      </section>
    </motion.div>
  );
}
