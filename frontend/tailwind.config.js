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
        },
        // Semantic Theme Role Tokens
        "app-bg": "var(--app-bg)",
        surface: {
          DEFAULT: "var(--surface)",
          secondary: "var(--surface-secondary)",
          elevated: "var(--surface-elevated)",
        },
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-tertiary": "var(--text-tertiary)",
        "border-main": "var(--border-main)",
        "border-subtle": "var(--border-subtle)",
        primary: {
          DEFAULT: "var(--primary)",
          hover: "var(--primary-hover)",
          soft: "var(--primary-soft)",
        },
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
        info: "var(--info)",
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
