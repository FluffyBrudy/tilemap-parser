import { useState } from "react";
import { motion } from "framer-motion";

interface CodeBlockProps {
  code: string;
}

export function CodeBlock({ code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative group rounded-lg overflow-hidden bg-zinc-950 border border-zinc-800"
    >
      <button
        onClick={handleCopy}
        className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 text-xs font-mono bg-zinc-800 hover:bg-zinc-700 rounded text-zinc-400"
      >
        {copied ? "copied" : "copy"}
      </button>
      <pre className="p-4 overflow-x-auto text-sm">
        <code className="font-mono text-zinc-300">{code}</code>
      </pre>
    </motion.div>
  );
}