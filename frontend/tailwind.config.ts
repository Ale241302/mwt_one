import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // S9-16 MWT Brand tokens
        navy:  { DEFAULT: '#013A57', light: '#0A4F75', dark: '#012840' },
        mint:  { DEFAULT: '#75CBB3', light: '#A0DACE', dark: '#5AB89E' },
        sand:  { DEFAULT: '#F5F0E8', dark: '#EAE3D2' },
        // Semantic (mapean a CSS vars para dark mode)
        surface: 'var(--surface)',
        mwt: {
          bg:           'var(--bg)',
          surface:      'var(--surface)',
          'text-primary':   'var(--text-primary)',
          'text-secondary': 'var(--text-secondary)',
          'text-muted':     'var(--text-muted)',
          interactive:  'var(--interactive)',
          border:       'var(--border)',
        },
        // Credit band colors
        credit: {
          'green-bg':   '#F0FAF6',
          'green-text': '#0E8A6D',
          'amber-bg':   '#FFF7ED',
          'amber-text': '#B45309',
          'red-bg':     '#FEF2F2',
          'red-text':   '#DC2626',
        },
      },
      fontFamily: {
        sans:    ['var(--font-general-sans)', 'Inter', 'system-ui', 'sans-serif'],
        display: ['var(--font-general-sans)', 'Inter', 'system-ui', 'sans-serif'],
        mono:    ['var(--font-geist-mono)', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm:  '4px',
        md:  '6px',
        lg:  '8px',
        xl:  '12px',
        '2xl': '16px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(1,58,87,0.04), 0 2px 8px -2px rgba(1,58,87,0.08)',
        md: '0 2px 4px rgba(1,58,87,0.06), 0 4px 16px -4px rgba(1,58,87,0.12)',
        lg: '0 4px 8px rgba(1,58,87,0.08), 0 8px 32px -8px rgba(1,58,87,0.16)',
      },
    },
  },
  plugins: [],
};

export default config;
