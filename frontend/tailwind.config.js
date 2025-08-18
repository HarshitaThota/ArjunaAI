/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        peacockBlue: "#006d77",
        peacockGreen: "#83c5be",
        gold: "#ffd166",
      },
    },
  },
  plugins: [],
};
