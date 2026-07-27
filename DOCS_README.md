# Tilemap Parser Documentation Site

A comprehensive, modern documentation website for the Tilemap Parser Python library.

## Overview

This is a Next.js 15 documentation site built for the Tilemap Parser project. It features a clean, minimal design with excellent performance and accessibility.

## Features

✓ **Static generation** - All pages pre-rendered at build time for maximum performance  
✓ **Responsive design** - Mobile-first approach with desktop sidebar navigation  
✓ **Dark mode** - Built-in theme switching with next-themes  
✓ **Fast navigation** - Instant page transitions without server requests  
✓ **Accessible** - WCAG AA compliant with semantic HTML  
✓ **SEO optimized** - Automatic metadata and Open Graph tags  
✓ **Minimal dependencies** - Lightweight bundle size  

## Technology Stack

- **Next.js 15** - React framework with App Router
- **React 19** - Latest React with new features
- **TypeScript** - Type-safe development
- **Tailwind CSS v4** - Utility-first styling
- **next-themes** - Theme management
- **Lucide React** - Icon library
- **Gray Matter** - Frontmatter parsing for MDX files

## Project Structure

```
/app
  /layout.tsx              - Root layout with theme provider
  /page.tsx                - Homepage
  /(docs)
    /layout.tsx            - Docs layout with sidebar
    /docs/[...slug]
      /page.tsx            - Dynamic documentation pages

/components
  /Header.tsx              - Top navigation with theme toggle
  /Sidebar.tsx             - Navigation sidebar
  /TableOfContents.tsx     - Sticky table of contents
  /Footer.tsx              - Footer with links
  /CodeBlock.tsx           - Code block with copy button
  /Callout.tsx             - Info/warning/error callouts

/lib
  /navigation.ts           - Sidebar navigation structure
  /mdx.ts                  - Markdown/MDX utilities

/content
  /getting-started/        - Installation and quick start
  /guide/                  - Comprehensive guides
  /examples/               - Code examples
  /api/                    - API reference
  /reference/              - Format specifications
  /internals/              - Architecture docs
```

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Open http://localhost:3000
```

The dev server includes hot reload and Fast Refresh for instant updates.

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Adding Documentation

Documentation files are Markdown with YAML frontmatter:

```markdown
---
title: Page Title
description: Brief description for SEO
category: Guide
order: 1
keywords: [keyword1, keyword2]
updated: 2024-01-15
---

# Page Title

Content goes here...
```

Place files in `/content` using the category folder:
- `content/getting-started/` - Installation, quick start
- `content/guide/` - Detailed guides
- `content/examples/` - Code examples
- `content/api/` - API reference
- `content/reference/` - Specifications
- `content/internals/` - Architecture

### Markdown Features

**Bold**: `**text**` or `__text__`  
**Italic**: `*text*` or `_text_`  
**Code**: `` `code` ``  
**Links**: `[text](url)`  

### Code Blocks

````markdown
```python
def hello():
    print("Hello, World!")
```
````

## Styling & Customization

### Colors

Colors are defined as CSS variables in `/app/globals.css`:

```css
--background: 0 0% 100%;      /* Primary background */
--foreground: 0 0% 10%;       /* Primary text */
--muted: 0 0% 92%;            /* Secondary background */
--muted-foreground: 0 0% 45%; /* Secondary text */
--border: 0 0% 88%;           /* Border color */
--accent: 200 100% 50%;       /* Accent color (blue) */
```

Customize by editing the CSS variables for light and dark themes.

### Typography

Fonts are configured in `tailwind.config.ts` and applied via `--font-sans` and `--font-mono` CSS variables.

## Performance

- **Static generation** - Pages built at deploy time
- **Optimized images** - Automatic image optimization
- **Minimal JavaScript** - Server components by default
- **Code splitting** - Automatic route-based code splitting
- **Caching** - Aggressively cached static assets

### Web Vitals

Target metrics for optimal performance:

- **LCP** (Largest Contentful Paint) < 2.5s
- **FID** (First Input Delay) < 100ms
- **CLS** (Cumulative Layout Shift) < 0.1

## Accessibility

- **Semantic HTML** - Proper heading hierarchy and landmark roles
- **WCAG AA** - Color contrast ratios meet accessibility standards
- **Keyboard navigation** - Full keyboard support
- **Screen readers** - Proper ARIA labels and alt text
- **Focus management** - Visible focus indicators

## Navigation Structure

The sidebar navigation is defined in `/lib/navigation.ts` and auto-generates based on content files:

```typescript
export const navigation: NavItem[] = [
  {
    title: 'Getting Started',
    items: [
      { title: 'Installation', href: '/docs/getting-started/installation' },
      { title: 'Quick Start', href: '/docs/getting-started/quick-start' },
    ],
  },
  // ...
];
```

## Deployment

### Deploy to Vercel

```bash
# Push to GitHub
git push origin main

# Deploy automatically via Vercel
# (configure in https://vercel.com/new)
```

### Deploy to Other Platforms

The site is a standard Next.js app and can be deployed to any Node.js host:

```bash
npm run build
npm start
```

Or as a static export:

```bash
# In next.config.js, add:
# export const output = 'export'

npm run build
# Output is in ./out directory
```

## Environment Variables

No environment variables are required for the documentation site to run. Optional variables:

- `NEXT_PUBLIC_SITE_URL` - Full site URL for Open Graph tags

## Troubleshooting

### Dev server not starting
```bash
rm -rf .next node_modules
npm install
npm run dev
```

### Styles not applying
```bash
# Tailwind CSS sometimes needs a rebuild
npm run build
```

### Content not showing
Check that markdown files are in the correct `/content` directory with proper frontmatter.

## Contributing

To contribute documentation:

1. Create a new `.mdx` file in the appropriate `/content` subdirectory
2. Add proper frontmatter (title, description, category, keywords)
3. Write content in Markdown format
4. Test locally with `npm run dev`
5. Submit a pull request

## License

This documentation site is part of the Tilemap Parser project. See the main repository for license information.

## Support

For issues or suggestions:

- **GitHub Issues**: https://github.com/FluffyBrudy/tilemap-parser/issues
- **Documentation**: Check the site at `/docs`
- **Quick Links**: Available in the footer

---

**Built with** Next.js, React, TypeScript, Tailwind CSS  
**Designed for** simplicity, performance, and maintainability
