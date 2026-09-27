# RWA Wire

**The intelligence layer for the tokenized economy.**

An independent media/research site covering real-world assets (RWA),
tokenization, institutional finance and crypto markets. Built with Astro,
TypeScript, Tailwind CSS and MDX. Fully static — no backend, no database —
and designed to deploy to GitHub Pages.

---

## 1. Project structure

```
rwa-wire/
├── .github/workflows/deploy.yml     # GitHub Pages CI/CD (build + deploy on push to main)
├── astro.config.mjs                 # Astro config — site URL, base path, integrations
├── tailwind.config.mjs              # Brand colors, fonts, typography plugin config
├── package.json
├── public/                          # Static files served as-is
│   ├── favicon.svg                  # "//" wire mark favicon
│   ├── logo-mark.svg                # Larger logo mark (export to PNG for Telegram avatar etc.)
│   ├── og-default.png               # Default social share image
│   ├── robots.txt
│   └── site.webmanifest
└── src/
    ├── config/site.ts               # ⭐ SINGLE SOURCE OF TRUTH: brand, nav, Telegram URL, affiliate URL
    ├── content/
    │   ├── config.ts                # Content collection schema for articles
    │   └── articles/*.mdx           # ⭐ ALL ARTICLE CONTENT LIVES HERE (24 sample articles)
    ├── components/                  # Header, Footer, ArticleCard, FeaturedArticle, CategoryCard,
    │                                 # ProjectCard, Tag, Breadcrumbs, TelegramCTA, TradingCTA,
    │                                 # DataCard, ToolCard, MobileMenu, RelatedArticles, SEO, Logo
    ├── layouts/
    │   ├── BaseLayout.astro         # Wraps every page (head, header, footer)
    │   ├── ArticleLayout.astro      # Wraps every article (meta, hero, takeaways, related, CTAs)
    │   └── ToolLayout.astro         # Wraps every calculator page
    ├── pages/
    │   ├── index.astro              # Homepage
    │   ├── [category]/index.astro   # Section listing pages (/news/, /rwa/, /tokenization/, etc.)
    │   ├── [category]/[slug].astro  # Individual article pages (/learn/what-is-tokenization/)
    │   ├── tools/                   # 4 calculators + tools index
    │   ├── about/, contact/, privacy/, terms/, affiliate-disclosure/
    │   └── 404.astro
    └── styles/global.css            # Fonts, base styles, design tokens
```

The `@astrojs/sitemap` integration generates `sitemap-index.xml` automatically
at build time; there's nothing to maintain manually.

---

## 2. Setup instructions

Requires **Node.js 18.17+** (Node 20 recommended) and npm.

```bash
git clone <your-repo-url> rwa-wire
cd rwa-wire
npm install
```

> The repository intentionally does not require a committed lockfile for the first GitHub Pages deployment.
> The GitHub Action uses `npm install`; after your first local install, commit the generated `package-lock.json` for fully reproducible builds.

---

## 3. Local development

```bash
npm run dev
```

Opens the site at `http://localhost:4321/rwa-wire/` (the `/rwa-wire/` base
path matches the GitHub Pages project-page config — see below).

Other scripts:

- `npm run build` — type-checks and builds the static site to `dist/`
- `npm run preview` — serves the built `dist/` locally to sanity-check the production build

---

## 4. GitHub Pages deployment

This project is pre-wired for GitHub Pages via `.github/workflows/deploy.yml`,
which builds and deploys automatically on every push to `main`.

**One-time setup:**

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages** and set **Source** to
   **GitHub Actions**.
3. Open `astro.config.mjs` and confirm two values:
   - `site`: your GitHub Pages domain, e.g. `https://your-username.github.io`
   - `base`: your repo name with leading/trailing slash, e.g. `/rwa-wire`
     (if you're deploying to a **user/org root page** or a **custom domain**
     instead of a project page, set `base: "/"` instead)
4. The internal site links already respect Astro's `base` setting. If you change the base path,
   review `public/site.webmanifest` and `public/robots.txt` for any absolute `/rwa-wire/` references.
5. Push to `main`. The Action builds and deploys automatically — check the
   **Actions** tab for progress, then find your live URL under **Settings → Pages**.

**Custom domain:** add a `public/CNAME` file containing your domain, and
update `site` in `astro.config.mjs` to that domain with `base: "/"`.

---

## 5. Where to edit articles

All article content lives in `src/content/articles/*.mdx` — one file per
article. Each file has frontmatter (title, description, category, dates,
tags, related articles, etc.) followed by the article body in Markdown/MDX.

To add a new article:

1. Duplicate an existing `.mdx` file in `src/content/articles/`.
2. Update the frontmatter — `category` must be one of `news`, `rwa`,
   `tokenization`, `institutions`, `markets`, `projects`, `learn`; `type`
   must be one of `NEWS`, `EXPLAINER`, `RESEARCH`, `MARKET`, `PROJECT`.
3. Write the body in Markdown. The filename (minus `.mdx`) becomes the
   article's URL slug, e.g. `my-article.mdx` → `/<category>/my-article/`.
4. To link related articles, add their slugs to `relatedSlugs`.
5. Set `showTradingCTA: true` only on market/trading-relevant articles, per
   the site's editorial policy — see `src/components/TradingCTA.astro`.

No code changes are required to publish a new article — the dynamic route
at `src/pages/[category]/[slug].astro` picks up every file automatically.

---

## 6. Where to change branding

Almost everything brand-related is centralized in **`src/config/site.ts`**:
site name, tagline, description, navigation labels/links, footer links, and
category labels/descriptions.

- **Colors & fonts:** `tailwind.config.mjs` (the `wire`, `bg`, `surface`,
  `ink` color tokens) and the font import at the top of `src/styles/global.css`.
- **Logo:** `src/components/Logo.astro` (text-based "RWA WIRE //" mark) and
  `public/favicon.svg` / `public/logo-mark.svg` for the icon mark. Export
  `logo-mark.svg` to PNG (e.g. via any online SVG-to-PNG tool, or
  `npx sharp-cli` locally) for a Telegram profile image.

---

## 7. Where to change the Telegram URL

Edit `TELEGRAM_URL` near the top of **`src/config/site.ts`**. Every
"Join Telegram" button and link across the header, footer, homepage CTA
section and every article's Telegram CTA updates automatically.

---

## 8. Where to change the affiliate CTA URL

Edit `AFFILIATE_URL` and `AFFILIATE_PARTNER_NAME` in **`src/config/site.ts`**.
The single `<TradingCTA />` component (`src/components/TradingCTA.astro`)
reads from these values, so changing them here updates every instance of
the CTA site-wide — no exchange name is hardcoded anywhere else in the
codebase. The CTA only renders on articles where the frontmatter sets
`showTradingCTA: true`.

---

## 9. Recommended next development steps

1. **Run `npm install` and `npm run build` locally** to confirm everything
   compiles cleanly in a real Node environment (this container had no
   network access to verify the install).
2. **Replace placeholder legal pages** (`/privacy/`, `/terms/`,
   `/affiliate-disclosure/`) with counsel-reviewed copy before launch.
3. **Replace placeholder URLs**: Telegram, X, contact email, and the
   affiliate link in `src/config/site.ts`.
4. **Add real hero images** for articles (`heroImage` frontmatter field) —
   currently omitted so the MVP has no placeholder/stock imagery.
5. **Expand content** beyond the 24 seed articles — the content collection
   scales without any code changes.
6. **Consider adding**: an RSS feed (`@astrojs/rss`), a search feature
   (e.g. Pagefind, which works well with static Astro sites), and a
   lightweight newsletter signup if RWA Wire wants an owned-audience channel
   beyond Telegram.
7. **CMS path**: if non-technical editors need a UI instead of editing MDX
   directly, a headless CMS like Tina CMS or Decap CMS can be layered on top
   of the existing `src/content/articles/` structure without changing the
   site's architecture.
