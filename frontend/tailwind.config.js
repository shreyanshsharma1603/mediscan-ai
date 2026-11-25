/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        navy: {
          950: "#050b16",
          900: "#071022",
          850: "#0b162d",
          800: "#0f1e3b",
          700: "#172b52",
        },
      },
    },
  },
  plugins: [],
};
