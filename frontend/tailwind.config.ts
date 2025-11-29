import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        // Pilldreams Design System
        pd: {
          // Backgrounds
          primary: '#000000',
          secondary: '#0a0a0a',
          card: '#111111',
          hover: '#1a1a1a',
          // Borders
          border: '#222222',
          'border-subtle': '#1a1a1a',
          // Text
          'text-primary': '#ffffff',
          'text-secondary': '#a1a1aa',
          'text-muted': '#71717a',
          'text-subtle': '#52525b',
          // Accent (Steel Blue)
          accent: '#60a5fa',
          'accent-secondary': '#3b82f6',
          'accent-muted': '#1d4ed8',
          // Score colors (Steel/Silver gradients - no traffic lights)
          'score-high': '#e2e8f0',      // Silver (high scores)
          'score-medium': '#94a3b8',    // Steel (medium scores)
          'score-low': '#64748b',       // Dark Steel (low scores)
          'score-darker': '#475569',    // Slate (lowest)
        }
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        // Aceternity-style glow gradient
        'glow-gradient': 'radial-gradient(61.17% 178.53% at 38.83% -13.54%, #3B3B3B 0%, #888787 12.61%, #FFFFFF 50%, #888787 80%, #3B3B3B 100%)',
        // Score gradients
        'score-high-gradient': 'linear-gradient(135deg, #e2e8f0, #94a3b8)',
        'score-medium-gradient': 'linear-gradient(135deg, #94a3b8, #64748b)',
        'score-low-gradient': 'linear-gradient(135deg, #64748b, #475569)',
      },
      boxShadow: {
        'glow-sm': '0 0 10px rgba(96, 165, 250, 0.1)',
        'glow-md': '0 0 20px rgba(96, 165, 250, 0.15)',
        'glow-lg': '0 0 30px rgba(96, 165, 250, 0.2)',
      }
    }
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
