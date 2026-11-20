/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#070b12", 900: "#0b111b", 800: "#111a28", 700: "#1a2638" },
        safety: { DEFAULT: "#f59e0b", soft: "#fbbf24" },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
