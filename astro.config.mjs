import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

export default defineConfig({
  site: "https://therwawire.com",
  base: "/",
  trailingSlash: "always",

  integrations: [
    mdx(),
  ],
});
