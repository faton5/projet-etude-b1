import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        leaf: "#2f6f4e",
        tomato: "#d84727",
        soil: "#5c4738",
        cream: "#f7f1e6",
        ink: "#18201b"
      },
      boxShadow: {
        soft: "0 18px 50px rgba(24, 32, 27, 0.10)"
      }
    }
  },
  plugins: []
};

export default config;
