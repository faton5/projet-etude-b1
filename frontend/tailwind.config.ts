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
        // AgroPulse colors
        leaf: "#2f6f4e",
        tomato: "#d84727",
        soil: "#5c4738",
        cream: "#f7f1e6",
        ink: "#17201b",
        mist: "#edf5f2",
        sky: "#2f6f88",
        // GardenCare design system tokens
        "primary": "#334f2b",
        "on-primary": "#ffffff",
        "primary-container": "#4a6741",
        "on-primary-container": "#c2e4b4",
        "primary-fixed": "#caecbc",
        "primary-fixed-dim": "#afd0a1",
        "on-primary-fixed": "#062104",
        "on-primary-fixed-variant": "#324e2a",
        "secondary": "#974725",
        "on-secondary": "#ffffff",
        "secondary-container": "#fe9970",
        "on-secondary-container": "#772f0e",
        "secondary-fixed": "#ffdbce",
        "secondary-fixed-dim": "#ffb598",
        "on-secondary-fixed": "#370e00",
        "on-secondary-fixed-variant": "#78310f",
        "tertiary": "#204c6a",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#3a6483",
        "on-tertiary-container": "#bbdfff",
        "tertiary-fixed": "#cbe6ff",
        "tertiary-fixed-dim": "#a2cbef",
        "on-tertiary-fixed": "#001e30",
        "on-tertiary-fixed-variant": "#1e4a68",
        "surface": "#fbf9f4",
        "surface-dim": "#dbdad5",
        "surface-bright": "#fbf9f4",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f5f3ee",
        "surface-container": "#f0eee9",
        "surface-container-high": "#eae8e3",
        "surface-container-highest": "#e4e2dd",
        "surface-variant": "#e4e2dd",
        "surface-tint": "#496640",
        "on-surface": "#1b1c19",
        "on-surface-variant": "#434840",
        "inverse-surface": "#30312e",
        "inverse-on-surface": "#f2f1ec",
        "inverse-primary": "#afd0a1",
        "background": "#fbf9f4",
        "on-background": "#1b1c19",
        "outline": "#73796f",
        "outline-variant": "#c3c8bd",
        "error": "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a"
      },
      fontFamily: {
        "headline-md": ["Atkinson Hyperlegible Next", "sans-serif"],
        "headline-lg": ["Atkinson Hyperlegible Next", "sans-serif"],
        "label-lg": ["Atkinson Hyperlegible Next", "sans-serif"],
        "body-lg": ["Atkinson Hyperlegible Next", "sans-serif"],
        "body-md": ["Atkinson Hyperlegible Next", "sans-serif"],
        "display-lg": ["Atkinson Hyperlegible Next", "sans-serif"],
        "display-lg-mobile": ["Atkinson Hyperlegible Next", "sans-serif"],
        "status-msg": ["Atkinson Hyperlegible Next", "sans-serif"],
        "status-msg-mobile": ["Atkinson Hyperlegible Next", "sans-serif"]
      },
      fontSize: {
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "headline-lg": ["32px", { lineHeight: "40px", fontWeight: "600" }],
        "label-lg": ["16px", { lineHeight: "20px", letterSpacing: "0.02em", fontWeight: "600" }],
        "body-lg": ["20px", { lineHeight: "30px", fontWeight: "400" }],
        "body-md": ["18px", { lineHeight: "26px", fontWeight: "400" }],
        "display-lg": ["40px", { lineHeight: "48px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-lg-mobile": ["32px", { lineHeight: "38px", fontWeight: "700" }],
        "status-msg": ["22px", { lineHeight: "28px", fontWeight: "700" }],
        "status-msg-mobile": ["20px", { lineHeight: "26px", fontWeight: "700" }]
      },
      spacing: {
        "xs": "4px",
        "sm": "12px",
        "base": "8px",
        "md": "24px",
        "lg": "40px",
        "xl": "64px",
        "2xl": "96px",
        "gutter": "24px",
        "container-margin": "32px"
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem"
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 32, 27, 0.10)",
        tight: "0 10px 24px rgba(23, 32, 27, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
