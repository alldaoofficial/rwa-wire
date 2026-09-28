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
    from:{kind:"institution",slug:"blackrock",label:"BlackRock"},
    to:{kind:"project",slug:"securitize-explained",label:"Securitize"},
    type:"strategic_investment", label:"Strategic investor",
    source:"https://investors.securitize.io/news/news-details/2024/Securitize-Announces-47-Million-Strategic-Funding-Round-Led-by-BlackRock-05-01-2024/default.aspx",
    sourceLabel:"Securitize funding announcement", asOf:"2024-05-01"
  }
];

export const relationshipsFor = (kind: EntityKind, slug: string) =>
  relationships.filter(r => (r.from.kind===kind && r.from.slug===slug) || (r.to.kind===kind && r.to.slug===slug));
