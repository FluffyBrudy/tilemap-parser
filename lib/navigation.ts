export interface NavItem {
  title: string;
  href?: string;
  items?: NavItem[];
  icon?: string;
}

export const navigation: NavItem[] = [
  {
    title: 'Getting Started',
    items: [
      {
        title: 'Installation',
        href: '/docs/getting-started/installation',
      },
      {
        title: 'Quick Start',
        href: '/docs/getting-started/quick-start',
      },
    ],
  },
  {
    title: 'Guide',
    items: [
      {
        title: 'Map Parsing',
        href: '/docs/guide/map-parsing',
      },
      {
        title: 'Collision Detection',
        href: '/docs/guide/collision-detection',
      },
      {
        title: 'Camera System',
        href: '/docs/guide/camera-system',
      },
      {
        title: 'Sprite Animations',
        href: '/docs/guide/sprite-animations',
      },
      {
        title: 'Particle Effects',
        href: '/docs/guide/particle-effects',
      },
    ],
  },
  {
    title: 'Examples',
    items: [
      {
        title: 'Basic Map Rendering',
        href: '/docs/examples/basic-rendering',
      },
      {
        title: 'Collision Handling',
        href: '/docs/examples/collision-handling',
      },
      {
        title: 'Advanced Usage',
        href: '/docs/examples/advanced-usage',
      },
    ],
  },
  {
    title: 'API Reference',
    items: [
      {
        title: 'Parser',
        href: '/docs/api/parser',
      },
      {
        title: 'Map Object',
        href: '/docs/api/map-object',
      },
      {
        title: 'Collision',
        href: '/docs/api/collision',
      },
    ],
  },
  {
    title: 'Reference',
    items: [
      {
        title: 'JSON Format',
        href: '/docs/reference/json-format',
      },
      {
        title: 'JSON Schema',
        href: '/docs/reference/json-schema',
      },
    ],
  },
  {
    title: 'Internals',
    items: [
      {
        title: 'Architecture',
        href: '/docs/internals/architecture',
      },
      {
        title: 'Design Decisions',
        href: '/docs/internals/design-decisions',
      },
    ],
  },
];
