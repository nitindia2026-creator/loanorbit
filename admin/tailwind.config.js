/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        orbit: {
          dark: '#0f172a',
          navy: '#1e293b',
          teal: '#0d9488',
          cyan: '#06b6d4',
          accent: '#10b981',
          bg: '#f8fafc',
          border: '#e2e8f0',
        }
      }
    },
  },
  plugins: [],
}
