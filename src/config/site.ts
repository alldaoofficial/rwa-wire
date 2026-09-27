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
  url: "https://alldaoofficial.github.io",
  base: "/rwa-wire",
  locale: "en_US",
  twitterHandle: "",
};

// Update this in one place to change where every "Join Telegram" / "Get the
// signal" button on the site points.
export const TELEGRAM_URL = "https://t.me/RWAWireHQ";

export const X_URL = "";

// -----------------------------------------------------------------------------
// Affiliate / trading CTA
//
// RWA Wire will eventually monetize through crypto exchange affiliate
// partnerships. Change AFFILIATE_URL and AFFILIATE_PARTNER_NAME here and every
// <TradingCTA /> on the site updates automatically. Nothing else in the
// codebase should hardcode an exchange name or affiliate link.
// -----------------------------------------------------------------------------
export const AFFILIATE_PARTNER_NAME = "Bitunix";
export const AFFILIATE_URL = "https://www.bitunix.com/register?vipCode=0xcrlt";

export const NAV_LINKS = [
  { label: "News", href: "/news/" },
  { label: "RWA", href: "/rwa/" },
  { label: "Tokenization", href: "/tokenization/" },
  { label: "Institutions", href: "/institutions/" },
  { label: "Markets", href: "/markets/" },
  { label: "Projects", href: "/projects/" },
  { label: "Learn", href: "/learn/" },
  { label: "Tools", href: "/tools/" },
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
  news: {
    label: "News",
    description: "Timely coverage of the tokenized economy.",
  },
  rwa: {
    label: "RWA",
    description: "Real-world assets moving onchain.",
  },
  tokenization: {
    label: "Tokenization",
    description: "How traditional assets become programmable.",
  },
  institutions: {
    label: "Institutions",
    description: "Banks, asset managers and financial infrastructure.",
  },
  markets: {
    label: "Markets",
    description: "Market developments and trading-relevant information.",
  },
  projects: {
    label: "Projects",
    description: "Neutral profiles of the infrastructure being built.",
  },
  learn: {
    label: "Learn",
    description: "Evergreen explainers on tokenization and RWAs.",
  },
};
