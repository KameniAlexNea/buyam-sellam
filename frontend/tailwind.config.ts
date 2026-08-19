import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        deep: "#0b0f1e",
        board: "#121a2e",
        card: "#182240",
        "card-hover": "#1e2d52",
        gold: "#ffcc00",
        buy: "#00e68a",
        sell: "#ff4d6a",
        dim: "#7a89aa",
        accent: "#4d94ff",
        violet: "#b366ff",
        cyan: "#00d4ff",
        amberc: "#ff9f1a",
      },
      fontFamily: {
        display: ["var(--font-orbitron)", "sans-serif"],
        body: ["var(--font-chakra)", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 32px rgba(0,0,0,0.5)",
        glow: "0 0 30px rgba(77,148,255,0.12)",
        "glow-gold": "0 0 30px rgba(255,204,0,0.16)",
      },
      keyframes: {
        "dice-roll": {
          "0%": { transform: "rotate(0deg) scale(1)" },
          "25%": { transform: "rotate(-12deg) scale(1.08)" },
          "50%": { transform: "rotate(8deg) scale(0.96)" },
          "75%": { transform: "rotate(-6deg) scale(1.05)" },
          "100%": { transform: "rotate(0deg) scale(1)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 8px rgba(0,230,138,0.25)" },
          "50%": { boxShadow: "0 0 22px rgba(0,230,138,0.6)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "dice-roll": "dice-roll 0.6s ease-in-out",
        "pulse-glow": "pulse-glow 1.6s ease-in-out infinite",
        "fade-in-up": "fade-in-up 0.4s ease-out",
        shimmer: "shimmer 2s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
