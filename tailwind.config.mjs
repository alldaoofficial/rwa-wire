/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#080A0D",
        surface: "#11151A",
        "surface-raised": "#161B22",
        line: "#1E252D",
        ink: "#F5F7FA",
        "ink-muted": "#8B949E",
        wire: {
          DEFAULT: "#2ED47A",
          dim: "#1F8F57",
          soft: "#173226",
        },
      },
      fontFamily: {
        serif: ["'Newsreader'", "ui-serif", "Georgia", "serif"],
        sans: ["'Inter'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      maxWidth: {
        content: "72ch",
        wire: "1280px",
      },
      typography: () => ({
        wire: {
          css: {
            "--tw-prose-body": "#C9D1D9",
            "--tw-prose-headings": "#F5F7FA",
            "--tw-prose-links": "#2ED47A",
            "--tw-prose-bold": "#F5F7FA",
            "--tw-prose-bullets": "#2ED47A",
            "--tw-prose-hr": "#1E252D",
            "--tw-prose-quotes": "#F5F7FA",
            "--tw-prose-quote-borders": "#2ED47A",
            "--tw-prose-code": "#F5F7FA",
            "--tw-prose-th-borders": "#1E252D",
            "--tw-prose-td-borders": "#1E252D",
            maxWidth: "68ch",
            a: { textDecoration: "none", fontWeight: "500" },
            "a:hover": { textDecoration: "underline" },
          },
        },
      }),
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
