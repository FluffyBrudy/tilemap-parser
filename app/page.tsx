import Link from 'next/link';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { ArrowRight, Code, Zap, BookOpen } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-24 sm:py-32 border-b border-border">
          <div className="container max-w-3xl">
            <div className="text-center">
              <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
                Tilemap Parser
              </h1>
              <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                A lightweight, production-ready parser for tilemap-editor JSON maps with runtime support for collision detection, camera systems, sprite animations, and particle effects.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <Link
                  href="/docs/getting-started/installation"
                  className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-accent text-accent-foreground font-semibold hover:opacity-90 transition-opacity"
                >
                  Get Started <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
                <a
                  href="https://github.com/FluffyBrudy/tilemap-parser"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center px-6 py-3 rounded-lg border border-border hover:bg-muted transition-colors"
                >
                  View on GitHub
                </a>
              </div>
            </div>

            {/* Quick Example */}
            <div className="bg-muted rounded-lg p-6 border border-border">
              <p className="text-sm font-semibold mb-3 text-muted-foreground">Quick Example</p>
              <pre className="text-sm overflow-x-auto">
                <code>{`import { parseMap } from 'tilemap-parser';

const map = parseMap(jsonData);
console.log(map.layers);
console.log(map.collisions);`}</code>
              </pre>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 sm:py-32 border-b border-border">
          <div className="container">
            <h2 className="text-3xl sm:text-4xl font-bold text-center mb-16">Features</h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-muted/50 rounded-lg p-8 border border-border">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                  <Code className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Easy to Use</h3>
                <p className="text-muted-foreground">
                  Simple API for parsing and working with tilemap data. Get started in minutes.
                </p>
              </div>

              <div className="bg-muted/50 rounded-lg p-8 border border-border">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-lg font-semibold mb-2">High Performance</h3>
                <p className="text-muted-foreground">
                  Optimized for production use with minimal overhead. Process large maps efficiently.
                </p>
              </div>

              <div className="bg-muted/50 rounded-lg p-8 border border-border">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                  <BookOpen className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Well Documented</h3>
                <p className="text-muted-foreground">
                  Comprehensive guides, examples, and API reference to help you build great things.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Documentation Categories */}
        <section className="py-24 sm:py-32 border-b border-border">
          <div className="container">
            <h2 className="text-3xl sm:text-4xl font-bold text-center mb-16">Documentation</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              <Link
                href="/docs/getting-started/installation"
                className="bg-muted/50 rounded-lg p-6 border border-border hover:border-accent transition-colors group"
              >
                <h3 className="text-lg font-semibold mb-2 group-hover:text-accent">Getting Started</h3>
                <p className="text-muted-foreground text-sm">
                  Installation instructions, quick start guide, and basic examples to get you up and running.
                </p>
              </Link>

              <Link
                href="/docs/guide/map-parsing"
                className="bg-muted/50 rounded-lg p-6 border border-border hover:border-accent transition-colors group"
              >
                <h3 className="text-lg font-semibold mb-2 group-hover:text-accent">Guides</h3>
                <p className="text-muted-foreground text-sm">
                  Deep dive into core concepts like map parsing, collision detection, and animation systems.
                </p>
              </Link>

              <Link
                href="/docs/examples/basic-rendering"
                className="bg-muted/50 rounded-lg p-6 border border-border hover:border-accent transition-colors group"
              >
                <h3 className="text-lg font-semibold mb-2 group-hover:text-accent">Examples</h3>
                <p className="text-muted-foreground text-sm">
                  Real-world examples from basic rendering to advanced usage patterns.
                </p>
              </Link>

              <Link
                href="/docs/api/parser"
                className="bg-muted/50 rounded-lg p-6 border border-border hover:border-accent transition-colors group"
              >
                <h3 className="text-lg font-semibold mb-2 group-hover:text-accent">API Reference</h3>
                <p className="text-muted-foreground text-sm">
                  Complete reference for all parser functions and runtime APIs.
                </p>
              </Link>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 sm:py-32">
          <div className="container text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-6">Ready to get started?</h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Read the documentation to learn everything you need to know about Tilemap Parser.
            </p>
            <Link
              href="/docs/getting-started/installation"
              className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-accent text-accent-foreground font-semibold hover:opacity-90 transition-opacity"
            >
              Start Learning <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
