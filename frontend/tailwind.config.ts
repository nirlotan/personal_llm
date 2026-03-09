import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#E0DDFE",
          dark: "#1E1B4B",
          primary: "#5B4EFA",
          glass: "rgba(255, 255, 255, 0.4)",
          glassBorder: "rgba(255, 255, 255, 0.6)",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(91, 78, 250, 0.3)",
        "glow-strong": "0 0 25px rgba(50, 20, 150, 0.5)",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};

export default config;
