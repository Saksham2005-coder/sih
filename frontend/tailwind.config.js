/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          ink: "#152536",
          porcelain: "#F4F6F8",
          teal: "#0E746B",
          "teal-light": "#E6F5F3",
          "teal-dark": "#0B5B54",
          amber: "#C5892B",
          "amber-light": "#FEF7ED",
          red: "#B9474F",
          "red-light": "#FDF2F2",
          border: "#DFE5E9",
          muted: "#526473",
          surface: "#FFFFFF",
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
