/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: 'var(--ink)',
        panel: 'var(--panel)',
        'panel-2': 'var(--panel-2)',
        raise: 'var(--raise)',
        line: 'var(--line)',
        'line-2': 'var(--line-2)',
        paper: 'var(--text)',
        mute: 'var(--mute)',
        red: 'var(--red)',
        amber: 'var(--amber)',
        teal: 'var(--teal)',
        blue: 'var(--blue)',
        purple: 'var(--purple)'
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        retro: ['"VT323"', 'monospace'],
        mono: ['"Space Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace']
      },
      boxShadow: {
        hard: '4px 4px 0 0 rgba(0,0,0,0.5)',
        'hard-sm': '3px 3px 0 0 rgba(0,0,0,0.5)',
        'hard-lg': '6px 6px 0 0 rgba(0,0,0,0.5)'
      },
      borderRadius: { DEFAULT: '0px' }
    }
  },
  plugins: []
}
