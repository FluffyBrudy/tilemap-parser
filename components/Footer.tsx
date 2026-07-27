export function Footer() {
  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="container py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-semibold mb-4">Documentation</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="/docs/getting-started/installation" className="hover:text-foreground">
                  Installation
                </a>
              </li>
              <li>
                <a href="/docs/guide/map-parsing" className="hover:text-foreground">
                  Guide
                </a>
              </li>
              <li>
                <a href="/docs/api/parser" className="hover:text-foreground">
                  API Reference
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="https://github.com/FluffyBrudy/tilemap-parser" target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
                  GitHub
                </a>
              </li>
              <li>
                <a href="https://github.com/FluffyBrudy/tilemap-parser/issues" target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
                  Issues
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Learn</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="/docs/examples/basic-rendering" className="hover:text-foreground">
                  Examples
                </a>
              </li>
              <li>
                <a href="/docs/reference/json-format" className="hover:text-foreground">
                  Reference
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Project</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="/" className="hover:text-foreground">
                  Home
                </a>
              </li>
              <li>
                <a href="/docs/internals/architecture" className="hover:text-foreground">
                  Architecture
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-border pt-8 flex flex-col sm:flex-row items-center justify-between text-sm text-muted-foreground">
          <p>&copy; 2024 Tilemap Parser. All rights reserved.</p>
          <p className="mt-4 sm:mt-0">Built with Next.js and React</p>
        </div>
      </div>
    </footer>
  );
}
