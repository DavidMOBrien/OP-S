/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F0F0F',
        surface: '#1A1A1A',
        'surface-light': '#252525',
        'surface-border': '#2A2A2A',
        'accent-primary': '#FFFFFF',
        'accent-bright': '#F5F5F5',
        'accent-positive': '#10B981',
        'accent-negative': '#EF4444',
        'accent-neutral': '#71717A',
        'text-primary': '#F5F5F5',
        'text-secondary': '#A3A3A3',
        'text-tertiary': '#737373',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        heading: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

