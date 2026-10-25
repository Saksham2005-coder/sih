/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          ink: "var(--brand-ink)",
          porcelain: "var(--brand-porcelain)",
          teal: "var(--brand-teal)",
          "teal-light": "var(--brand-teal-light)",
          "teal-dark": "var(--brand-teal-dark)",
          amber: "var(--brand-amber)",
          "amber-light": "var(--brand-amber-light)",
          red: "var(--brand-red)",
          "red-light": "var(--brand-red-light)",
          border: "var(--brand-border)",
          muted: "var(--brand-muted)",
          surface: "var(--brand-surface)",
          "surface-secondary": "var(--brand-surface-secondary)",
          "surface-elevated": "var(--brand-surface-elevated)",
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
}
