import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { allClasses, allFunctions } from "../config";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type SearchResult = {
  path: string;
  name: string;
  type: "function" | "class" | "section";
  description: string;
};

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, results.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
      }
      if (e.key === "Enter" && results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose, selectedIndex, query]);

  const allItems: SearchResult[] = [
    { path: "/", name: "Home", type: "section", description: "Documentation home" },
    { path: "/installation", name: "Installation", type: "section", description: "How to install tilemap-parser" },
    { path: "/quickstart", name: "Quick Start", type: "section", description: "Basic usage examples" },
    { path: "/api", name: "API Reference", type: "section", description: "Complete API documentation" },
    { path: "/collision", name: "Collision", type: "section", description: "Tile and character collision" },
    { path: "/collision-runner", name: "Collision Runner", type: "section", description: "Ready-to-use collision system" },
    { path: "/json-formats", name: "JSON Formats", type: "section", description: "JSON format specifications" },
    { path: "/technical", name: "Technical Docs", type: "section", description: "Architecture and internals" },
    ...allFunctions.map(f => ({ path: "/api", name: f.name, type: "function" as const, description: f.description })),
    ...allClasses.map(c => ({ path: "/api", name: c.name, type: "class" as const, description: c.description })),
  ];

  const results = query.length < 2
    ? []
    : allItems.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase()) ||
        item.description.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 12);

  const handleSelect = (result: SearchResult) => {
    navigate(result.path);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center pt-[15vh]"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="bg-zinc-900 border border-zinc-700 rounded-lg w-full max-w-lg shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            placeholder="Search docs, functions, classes..."
            className="w-full px-4 py-3 bg-transparent text-zinc-100 placeholder-zinc-500 outline-none text-sm"
          />
          {results.length > 0 && (
            <div className="border-t border-zinc-800 max-h-96 overflow-y-auto">
              {results.map((result, i) => (
                <button
                  key={`${result.type}-${result.name}`}
                  onClick={() => handleSelect(result)}
                  onMouseEnter={() => setSelectedIndex(i)}
                  className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                    i === selectedIndex ? "bg-zinc-800" : "hover:bg-zinc-800/50"
                  }`}
                >
                  <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${
                    result.type === "function" ? "bg-green-900/50 text-green-400" :
                    result.type === "class" ? "bg-blue-900/50 text-blue-400" :
                    "bg-zinc-700 text-zinc-400"
                  }`}>
                    {result.type}
                  </span>
                  <div className="min-w-0">
                    <div className="text-sm text-zinc-100 font-medium">{result.name}</div>
                    <div className="text-xs text-zinc-500 truncate">{result.description}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
          {query.length >= 2 && results.length === 0 && (
            <div className="px-4 py-8 text-center text-zinc-500 text-sm">
              No results for "{query}"
            </div>
          )}
          <div className="border-t border-zinc-800 px-4 py-2 flex justify-between text-xs text-zinc-600">
            <span>ESC to close</span>
            <span>↑↓ to navigate · Enter to select</span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}