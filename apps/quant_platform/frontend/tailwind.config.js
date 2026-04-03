/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { 900: '#0a0e17', 800: '#111827', 700: '#1a2235' },
        accent: { 500: '#3b82f6', 400: '#60a5fa', 600: '#2563eb' },
        up: '#ef4444',
        down: '#22c55e',
        gold: '#f59e0b',
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
