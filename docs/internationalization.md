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

Translate the checked English source, preserving numeric values, sources, qualifications and material risk disclosures. Add a route group only after all referenced translations exist, include it in the sitemap generator and integration checks, and label English fallbacks. Keep translations in sync when the original's facts change. Do not change campaign promises or translate unresolved campaign terms as confirmed facts.

Reference: https://developers.google.com/search/docs/specialty/international/localized-versions
