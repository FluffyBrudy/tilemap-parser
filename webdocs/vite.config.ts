import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { defineConfig, type ViteDevServer, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

function devSearchIndex(): Plugin {
  return {
    name: "dev-search-index",
    configureServer(server: ViteDevServer) {
      const root = server.config.root;
      const indexFile = path.join(root, "dist", "search-index.json");

      const buildIndex = (): Promise<string> =>
        new Promise((resolve, reject) => {
          const child = spawn(
            process.execPath,
            [path.join(root, "scripts", "build-prerender.mjs"), "--index-only"],
            { cwd: root, env: process.env },
          );
          let out = "";
          child.on("error", reject);
          child.stderr?.on("data", (chunk: Buffer) => {
            out += chunk;
          });
          child.on("close", (code) => {
            if (code === 0) {
              try {
                resolve(readFileSync(indexFile, "utf8"));
              } catch (error) {
                reject(error);
              }
            } else {
              reject(new Error(out.trim() || `build exited with ${code}`));
            }
          });
        });

      let pending: Promise<string> | null = null;
      let stale = false;
      const getIndex = (): Promise<string> => {
        if (pending) return pending;
        try {
          if (!stale) return Promise.resolve(readFileSync(indexFile, "utf8"));
        } catch {
          // fall through: no index yet, build one
        }
        stale = false;
        pending = buildIndex().finally(() => {
          pending = null;
          if (stale) {
            void getIndex().catch(() => { });
          }
        });
        return pending;
      };

      void getIndex().catch(() => { });
      server.watcher.on("change", (file: string) => {
        if (file.startsWith(path.join(root, "src"))) {
          stale = true;
          if (!pending) {
            void getIndex().catch(() => { });
          }
        }
      });
      server.middlewares.use("/search-index.json", (_req, res) => {
        getIndex()
          .then((body) => {
            res.writeHead(200, { "content-type": "application/json" });
            res.end(body);
          })
          .catch((error: unknown) => {
            res.writeHead(500, { "content-type": "text/plain" });
            res.end(`search index failed: ${error}`);
          });
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), devSearchIndex()],
  server: {
    fs: {
      allow: [
        fileURLToPath(new URL(".", import.meta.url)),
        fileURLToPath(new URL("../examples", import.meta.url)),
      ],
    },
  },
});
