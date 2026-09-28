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
    from:{kind:"institution",slug:"franklin-templeton",label:"Franklin Templeton"},
    to:{kind:"asset",slug:"benji",label:"BENJI"},
    type:"manages", label:"Fund manager",
    source:"https://www.franklintempleton.com/press-releases/news-room/2026/franklin-templeton-stellar-development-foundation-mark-five-years-of-benji-the-first-u.s.-registered-tokenized-money-market-fund",
    sourceLabel:"Franklin Templeton BENJI announcement", asOf:"2026-04-30"
  },
  {
    from:{kind:"asset",slug:"benji",label:"BENJI"},
    to:{kind:"network",slug:"stellar",label:"Stellar"},
    type:"issued_on", label:"Original public blockchain",
    source:"https://www.franklintempleton.com/press-releases/news-room/2026/franklin-templeton-stellar-development-foundation-mark-five-years-of-benji-the-first-u.s.-registered-tokenized-money-market-fund",
    sourceLabel:"Franklin Templeton BENJI announcement", asOf:"2026-04-30"
  },
  {
    from:{kind:"institution",slug:"jpmorgan",label:"JPMorgan"},
    to:{kind:"asset",slug:"jpm-coin",label:"JPM Coin"},
    type:"manages", label:"Issuer",
    source:"https://www.jpmorgan.com/kinexys/jpm-coin",
    sourceLabel:"J.P. Morgan JPM Coin product page", asOf:"2026-04-28"
  },
  {
    from:{kind:"asset",slug:"jpm-coin",label:"JPM Coin"},
    to:{kind:"network",slug:"base",label:"Base"},
    type:"issued_on", label:"Public blockchain rail",
    source:"https://www.jpmorgan.com/payments/newsroom/kinexys-milestones-2026",
    sourceLabel:"Kinexys 2026 milestones", asOf:"2026-04-28"
  },
  {
    from:{kind:"institution",slug:"dtcc",label:"DTCC"},
    to:{kind:"network",slug:"stellar",label:"Stellar"},
    type:"issued_on", label:"Planned tokenization-service network",
    source:"https://www.dtcc.com/press-releases/2026/tokenization-service-to-connect-with-stellar-public-blockchain-as-dtc-advances-multi-chain-strategy",
    sourceLabel:"DTCC multi-chain announcement", asOf:"2026-05-27"
  },

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
