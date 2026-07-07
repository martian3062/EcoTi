import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Crimson Light Cloudy palette
        cream: "#faf7f5",
        cream2: "#f3eeeb",
        peach: "#f0e8e3",
        ink: "#1c1917",
        ink2: "#57534e",
        ink3: "#a8a29e",
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
