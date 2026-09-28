import { defineCollection, z } from "astro:content";

const articles = defineCollection({
  type: "content",
  schema: z.object({
    // One of the five supported article types.
    type: z.enum(["NEWS", "EXPLAINER", "RESEARCH", "MARKET", "PROJECT"]),
    // Primary section the article lives under (drives the URL prefix and nav highlighting).
    category: z.enum([
      "news",
      "rwa",
      "tokenization",
      "institutions",
      "markets",
      "projects",
      "learn",
    ]),
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default("RWA Wire Research"),
    readingTime: z.string(), // e.g. "5 min read"
    heroImage: z.string().optional(),
    heroImageAlt: z.string().optional(),
    tags: z.array(z.string()).default([]),
    // Optional structured intelligence fields used by PROJECT profiles.
    projectMeta: z.object({
      sector: z.string(),
      role: z.string(),
      assetExposure: z.string(),
      networks: z.array(z.string()).default([]),
      products: z.array(z.string()).default([]),
      status: z.string().default("Active"),
    }).optional(),
    // Slugs of related articles (must match the MDX filename without extension).
    relatedSlugs: z.array(z.string()).default([]),
    // Show the affiliate/trading CTA on this article. Off by default; only
    // relevant on market/trading-adjacent content per the brief.
    showTradingCTA: z.boolean().default(false),
    // Key takeaways rendered above the related-articles module.
    keyTakeaways: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { articles };
