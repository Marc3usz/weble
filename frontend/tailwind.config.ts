import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        black: '#000000',
        platinum: '#f4f4f6',
        "alabaster-grey": '#e6e6e9',
        "dim-grey": '#66666e',
        "rosy-granite": '#9999a1',
      },
      backgroundColor: {
        black: '#000000',
        platinum: '#f4f4f6',
        "alabaster-grey": '#e6e6e9',
        "dim-grey": '#66666e',
        "rosy-granite": '#9999a1',
      },
      textColor: {
        black: '#000000',
        "dim-grey": '#66666e',
        "rosy-granite": '#9999a1',
      },
      borderColor: {
        "alabaster-grey": '#e6e6e9',
        "dim-grey": '#66666e',
      },
    },
  },
  plugins: [],
};

export default config;
