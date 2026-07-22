import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Crimson DARK palette (text tokens are light for the dark-red theme)
        cream: "#faf7f5",
        cream2: "#f3eeeb",
        peach: "#f0e8e3",   // still light — used only for the graph canvases
        ink: "#fdeef5",     // main text (near-white pink)
        ink2: "#e7c9dc",    // secondary text
        ink3: "#b98fab",    // muted text
        crimson: "#dc2626",
        rose: "#e11d48",
        rosegold: "#b76e79",
        // semantic
        accent: "#dc2626",
        ok: "#059669",
        warn: "#d97706",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
