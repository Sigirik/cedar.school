/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    "bg-red-200",
    "bg-yellow-200",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
