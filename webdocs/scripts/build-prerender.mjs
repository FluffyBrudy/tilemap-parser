import { build } from "vite";
import { execFileSync } from "node:child_process";
import path from "node:path";

const root = process.cwd();
const entry = path.join(root, "scripts", "prerender.tsx");
const outDir = path.join(root, "dist", ".prerender");

await build({
  root,
  configFile: false,
  logLevel: "error",
  build: {
    ssr: entry,
    outDir,
    emptyOutDir: true,
    minify: false,
  },
});

execFileSync(process.execPath, [path.join(outDir, "prerender.js")], {
  stdio: "inherit",
  cwd: root,
});