import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";

// ---------------------------------------------------------------------------
// GitHub Pages configuration
//
// If you deploy to  https://<username>.github.io/<repo>/  (project page):
//   - set `site` to https://<username>.github.io
//   - set `base` to /<repo>
//
// If you deploy to  https://<username>.github.io/  (user/org root page)
// or to a custom domain:
//   - set `site` to your full domain
//   - set `base` to "/" (or remove it)
// ---------------------------------------------------------------------------
export default defineConfig({
  site: "https://your-username.github.io",
  base: "/rwa-wire",
  trailingSlash: "always",
  integrations: [
    mdx(),
    sitemap(),
  ],
});
