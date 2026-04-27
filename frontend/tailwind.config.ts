import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        black: {
          DEFAULT: "#08090a",
          100: "#020202",
          200: "#040405",
          300: "#050607",
          400: "#070809",
          500: "#08090a",
          600: "#353b42",
          700: "#606c78",
          800: "#929da8",
          900: "#c9ced3",
        },
        gold: {
          DEFAULT: "#d4af37",
          50: "#fef9f0",
          100: "#fef1e6",
          200: "#fce4c8",
          300: "#fad7aa",
          400: "#f7c66f",
          500: "#d4af37",
          600: "#c99e2e",
          700: "#a67d25",
          800: "#7a5a1a",
          900: "#4d3610",
        },
        lilac_ash: {
          DEFAULT: "#a7a2a9",
          100: "#222022",
          200: "#434045",
          300: "#655f67",
          400: "#878089",
          500: "#a7a2a9",
          600: "#b9b5ba",
          700: "#cac7cc",
          800: "#dcdadd",
          900: "#edecee",
        },
        bright_snow: {
          DEFAULT: "#f4f7f5",
          100: "#29392e",
          200: "#52725d",
          300: "#82a48d",
          400: "#bacdc1",
          500: "#f4f7f5",
          600: "#f6f8f6",
          700: "#f8faf9",
          800: "#fafcfb",
          900: "#fdfdfd",
        },
        charcoal: {
          DEFAULT: "#575a5e",
          100: "#111213",
          200: "#222425",
          300: "#333538",
          400: "#45474a",
          500: "#575a5e",
          600: "#767a7f",
          700: "#989ba0",
          800: "#babcbf",
          900: "#dddedf",
        },
        carbon_black: {
          DEFAULT: "#222823",
          100: "#070807",
          200: "#0e110e",
          300: "#151916",
          400: "#1c211d",
          500: "#222823",
          600: "#4b584d",
          700: "#738776",
          800: "#a1afa4",
          900: "#d0d7d1",
        },
      },
      borderRadius: {
        squircle: "20%",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
      },
      spacing: {
        // Using default Tailwind spacing (4px base unit)
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
