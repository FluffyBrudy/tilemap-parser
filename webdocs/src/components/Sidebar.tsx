import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { apiConfig } from "../config";

interface SidebarProps {
  onSearchOpen: () => void;
}

const navItems = [
  { path: "/", label: "Home" },
  { path: "/installation", label: "Installation" },
  { path: "/quickstart", label: "Quick Start" },
  { path: "/api", label: "API Reference" },
  { path: "/collision", label: "Collision", children: [
    { id: "overview", label: "Overview" },
    { id: "functions", label: "Functions" },
    { id: "data", label: "Data Classes" },
    { id: "shapes", label: "Shapes" },
    { id: "cache", label: "CollisionCache" },
  ]},
  { path: "/collision-runner", label: "Collision Runner", children: [
    { id: "overview", label: "Overview" },
    { id: "movement", label: "MovementMode" },
    { id: "result", label: "CollisionResult" },
    { id: "runner", label: "CollisionRunner" },
    { id: "setup", label: "Setup" },
  ]},
  { path: "/json-formats", label: "JSON Formats" },
  { path: "/technical", label: "Technical Docs" },
];

export function Sidebar({ onSearchOpen }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + "/");

  const handleNav = (path: string) => {
    navigate(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSectionNav = (basePath: string, sectionId: string) => {
    navigate(`${basePath}/${sectionId}`);
    setTimeout(() => {
      const el = document.getElementById(sectionId);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-56 h-screen fixed left-0 top-0 bg-zinc-950 border-r border-zinc-800 overflow-y-auto pb-8"
    >
      <div className="p-4 border-b border-zinc-800">
        <h1 className="font-semibold text-zinc-100">{apiConfig.packageName}</h1>
        <p className="text-xs text-zinc-500 mt-1">v{apiConfig.version}</p>
      </div>
      <button
        onClick={onSearchOpen}
        className="w-full mx-4 my-3 px-3 py-2 text-sm text-zinc-500 bg-zinc-800/50 hover:bg-zinc-800 rounded flex items-center gap-2"
      >
        <span className="text-xs opacity-60">⌘K</span>
        <span>Search</span>
      </button>
      <nav className="p-4 space-y-1">
        {navItems.map((item) => (
          <div key={item.path}>
            <button
              onClick={() => handleNav(item.path)}
              className={`w-full text-left px-3 py-2 text-sm rounded flex items-center gap-2 transition-colors ${
                isActive(item.path)
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              {item.label}
            </button>
            {item.children && isActive(item.path) && (
              <div className="ml-6 mt-1 space-y-1">
                {item.children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => handleSectionNav(item.path, child.id)}
                    className="w-full text-left px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    {child.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </motion.aside>
  );
}