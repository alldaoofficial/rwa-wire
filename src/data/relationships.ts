export type EntityKind = "institution" | "project" | "asset" | "network";
export type RelationshipType = "manages" | "tokenized_by" | "issued_on" | "strategic_investment";

export interface IntelligenceRelationship {
  from: { kind: EntityKind; slug: string; label: string };
  to: { kind: EntityKind; slug: string; label: string };
  type: RelationshipType;
  label: string;
  source: string;
  sourceLabel: string;
  asOf: string;
}

export const relationships: IntelligenceRelationship[] = [
  {
    from:{kind:"institution",slug:"blackrock",label:"BlackRock"},
    to:{kind:"asset",slug:"buidl",label:"BUIDL"},
    type:"manages", label:"Investment manager",
    source:"https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx",
    sourceLabel:"Securitize launch announcement", asOf:"2024-03-20"
  },
  {
    from:{kind:"asset",slug:"buidl",label:"BUIDL"},
    to:{kind:"project",slug:"securitize-explained",label:"Securitize"},
    type:"tokenized_by", label:"Tokenization platform & transfer agent",
    source:"https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx",
    sourceLabel:"Securitize launch announcement", asOf:"2024-03-20"
  },
  {
    from:{kind:"asset",slug:"buidl",label:"BUIDL"},
    to:{kind:"network",slug:"ethereum",label:"Ethereum"},
    type:"issued_on", label:"Original public blockchain",
    source:"https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx",
    sourceLabel:"Securitize launch announcement", asOf:"2024-03-20"
  },

  {
    from:{kind:"asset",slug:"buidl",label:"BUIDL"},
    to:{kind:"network",slug:"solana",label:"Solana"},
    type:"issued_on", label:"Additional share-class network",
    source:"https://investors.securitize.io/news/news-details/2025/BlackRock-and-Securitize-Debut-New-BUIDL-Share-Class-on-Solana-Network-03-25-2025/default.aspx",
    sourceLabel:"Securitize Solana announcement", asOf:"2025-03-25"
  },
  {
    from:{kind:"asset",slug:"buidl",label:"BUIDL"},
    to:{kind:"network",slug:"bnb-chain",label:"BNB Chain"},
    type:"issued_on", label:"Additional share-class network",
    source:"https://investors.securitize.io/news/news-details/2025/BlackRocks-BUIDL-Tokenized-by-Securitize-Now-Accepted-as-Collateral-for-Trading-on-Binance-and-Launches-on-BNB-Chain-11-14-2025/default.aspx",
    sourceLabel:"Securitize BNB Chain announcement", asOf:"2025-11-14"
  },
  {
    from:{kind:"asset",slug:"buidl",label:"BUIDL"},
    to:{kind:"network",slug:"tempo",label:"Tempo"},
    type:"issued_on", label:"Supported network",
    source:"https://investors.securitize.io/news/news-details/2026/Tempo-expands-onchain-yield-offering-with-BlackRocks-BUIDL-fund/default.aspx",
    sourceLabel:"Securitize / Tempo announcement", asOf:"2026-07-30"
  },
  {
    from:{kind:"institution",slug:"blackrock",label:"BlackRock"},
    to:{kind:"project",slug:"securitize-explained",label:"Securitize"},
    type:"strategic_investment", label:"Strategic investor",
    source:"https://investors.securitize.io/news/news-details/2024/Securitize-Announces-47-Million-Strategic-Funding-Round-Led-by-BlackRock-05-01-2024/default.aspx",
    sourceLabel:"Securitize funding announcement", asOf:"2024-05-01"
  }
];

export const relationshipsFor = (kind: EntityKind, slug: string) =>
  relationships.filter(r => (r.from.kind===kind && r.from.slug===slug) || (r.to.kind===kind && r.to.slug===slug));
