export type NavItem = { to: string; label: string }
export type NavGroup = { title: string; items: NavItem[] }

export const NAV: NavGroup[] = [
  {
    title: 'START',
    items: [
      { to: '/', label: 'Home' },
      { to: '/install', label: 'Installation' },
      { to: '/quick-start', label: 'Quick Start' }
    ]
  },
  {
    title: 'GUIDES',
    items: [
      { to: '/physics', label: 'Physics & Bodies' },
      { to: '/runner', label: 'CollisionRunner' },
      { to: '/object-collision', label: 'Object Collision' },
      { to: '/pipeline', label: 'The Pipeline' },
      { to: '/map-parsing', label: 'Map Parsing & Rendering' },
      { to: '/animations', label: 'Animations' },
      { to: '/camera', label: 'Camera' },
      { to: '/particles', label: 'Particles' },
      { to: '/pathfinding', label: 'Pathfinding' }
    ]
  },
  {
    title: 'EXAMPLES',
    items: [
      { to: '/examples', label: 'Examples' },
      { to: '/examples/full-physics-world', label: 'Full Physics World' },
      { to: '/examples/full-collision', label: 'Full Collision' },
      { to: '/examples/full-pathfinding', label: 'Full Pathfinding' }
    ]
  },
  {
    title: 'REFERENCE',
    items: [
      { to: '/api', label: 'API Reference' },
      { to: '/json', label: 'JSON Formats' },
      { to: '/notes', label: 'Technical Notes' }
    ]
  }
]

export const FLAT: NavItem[] = NAV.flatMap((g) => g.items)
export const VERSION = '5.0.3'
export const REPO = 'https://github.com/FluffyBrudy/tilemap-parser'
