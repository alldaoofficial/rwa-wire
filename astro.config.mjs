import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://alldaoofficial.github.io",
  base: "/rwa-wire",
  trailingSlash: "always",

  integrations: [
    mdx(),
    sitemap(),
  ],
});
