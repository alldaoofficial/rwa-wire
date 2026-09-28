// -----------------------------------------------------------------------------
// RWA WIRE — global site configuration
//
// This file is the single source of truth for brand strings, navigation,
// the Telegram destination, and the affiliate/trading CTA destination.
// Edit values here rather than hunting through components/pages.
// -----------------------------------------------------------------------------

export const SITE = {
  name: "RWA Wire",
  shortName: "RWA WIRE",
  tagline: "The intelligence layer for the tokenized economy.",
  description:
    "News, research and explainers on real-world assets, tokenization and the infrastructure transforming global finance.",
  // Used for canonical URLs / Open Graph / sitemap. Must match astro.config.mjs `site`.
  url: "https://therwawire.com",
  base: "/",
  locale: "en_US",
  twitterHandle: "@RWAWireHQ",
};

export const TELEGRAM_URL = "https://t.me/RWAWireHQ";
export const X_URL = "https://x.com/RWAWireHQ";

export const AFFILIATE_PARTNER_NAME = "Bitunix";
export const AFFILIATE_URL = "https://www.bitunix.com/register?vipCode=0xcrlt";

export const NAV_LINKS = [
  { label: "News", href: "/news/" },
  { label: "Markets", href: "/markets/" },
  { label: "Map", href: "/map/" },
  { label: "Projects", href: "/projects/" },
  { label: "Institutions", href: "/institutions/" },
  { label: "Learn", href: "/learn/" },
];

export const FOOTER_LINKS = [
  { label: "About", href: "/about/" },
  { label: "Contact", href: "/contact/" },
  { label: "Privacy", href: "/privacy/" },
  { label: "Terms", href: "/terms/" },
  { label: "Affiliate Disclosure", href: "/affiliate-disclosure/" },
];

export type CategorySlug =
  | "news"
  | "rwa"
  | "tokenization"
  | "institutions"
  | "markets"
  | "projects"
  | "learn";

export const CATEGORIES: Record<
  CategorySlug,
  { label: string; description: string }
> = {
  news: { label: "News", description: "Timely coverage of the tokenized economy." },
  rwa: { label: "RWA", description: "Real-world assets moving onchain." },
  tokenization: { label: "Tokenization", description: "How traditional assets become programmable." },
  institutions: { label: "Institutions", description: "Banks, asset managers and financial infrastructure." },
  markets: { label: "Markets", description: "Market developments and trading-relevant information." },
  projects: { label: "Projects", description: "Neutral profiles of the infrastructure being built." },
  learn: { label: "Learn", description: "Evergreen explainers on tokenization and RWAs." },
};
