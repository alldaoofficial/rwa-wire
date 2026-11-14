/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0B1015",
        surface: "#121A21",
        "surface-raised": "#1B2630",
        line: "#2A3640",
        ink: "#F0F5F4",
        "ink-muted": "#A2AFB8",
        wire: {
          DEFAULT: "#55DBA1",
          dim: "#26976C",
          soft: "#173D33",
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
