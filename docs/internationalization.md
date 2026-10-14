# RWA Wire language rollout

English remains at existing URLs. German, Spanish and French use `/de/`, `/es/` and `/fr/`. Initial scope: language landing pages, RWA explainer, Bitunix platform guide and newsletter signup (12 localized pages).

News and legal pages currently remain English and are labeled accordingly. Weekly newsletters and confirmation/unsubscribe emails remain English; localized signup consent states this explicitly. No subscriber language preference is stored or inferred, and no sending controls or backend consent logic are changed.

## Content and navigation

- `src/i18n/copy.json`: navigation, landing copy and signup/error strings.
- `src/i18n/guides.json`: localized RWA and Bitunix guide sections based on their English originals.
- `src/i18n/routes.ts`: the four supported translation groups. Unsupported articles do not receive misleading hreflang tags; the language menu explicitly offers localized homepages instead.
- Localized articles link to their English originals. Legal links are labeled as English.
- No automatic browser-language redirects. Readers choose their language.
- The paused Bitunix campaign in PR 23 is not activated or translated by this rollout.

## SEO and verification

Every translated group includes reciprocal absolute `hreflang` links, including itself and an English `x-default`. Each page retains a self canonical, correct HTML language and Open Graph locale. Localized URLs are included in the generated sitemap.

`npm run build` also runs `scripts/verify-i18n.mjs`, checking the 16 English/localized route variants, reciprocal alternates, canonicals, sitemap membership, localized internal destinations, affiliate attribution, and required unchecked consent when forms are enabled. Existing newsletter tests cover backend behavior.

Visual browser verification was unavailable in the execution environment; generated HTML and type-check/build validation were completed. No claim of native-speaker review or fully translated news coverage is made.

## Extending coverage

Second rollout: compact localized guides to tokenized US Treasuries and tokenized stocks, complete localized versions of the Koscom showcase report (13 October 2026) and IMF research discussion (11 October 2026), and localized news indexes. Each keeps its English source date, original link and applicable update date. News source links and the IMF correction are retained. Condensed guides are explicitly labeled; no claim of full verbatim translation is made.

The homepage prefers available translated headlines and destinations while clearly labeling English fallback articles. Localized news indexes contain only completed translations, with an English link for full ongoing coverage. New discoveries are not automatically translated or marked reviewed by this change.

The generated-output check now covers 36 English/localized routes and all reciprocal language links. Original sources for this rollout are `src/content/articles/tokenized-treasuries-explained.mdx`, `tokenized-stocks-explained.mdx`, `koscom-token-securities-platform-korea-fintech-week-2026.mdx` and `imf-deputy-director-says-tokenized-securities-should-settle-in-central-bank-money-not-stablecoins.mdx`. Updates to those originals require checking `src/i18n/articles.json` for factual consistency.

Translate the checked English source, preserving numeric values, sources, qualifications and material risk disclosures. Add a route group only after all referenced translations exist, include it in the sitemap generator and integration checks, and label English fallbacks. Keep translations in sync when the original's facts change. Do not change campaign promises or translate unresolved campaign terms as confirmed facts.

Reference: https://developers.google.com/search/docs/specialty/international/localized-versions
