export interface AssetIntelligence {
  slug: string;
  name: string;
  fullName: string;
  assetClass: string;
  manager: string;
  tokenizationPlatform: string;
  exposure: string;
  access: string;
  networks: string[];
  status: "Active" | "Monitoring";
  summary: string;
  primarySource: string;
  sourceLabel: string;
  asOf: string;
}

export const assets: AssetIntelligence[] = [
  {
    slug:"buidl",
    name:"BUIDL",
    fullName:"BlackRock USD Institutional Digital Liquidity Fund",
    assetClass:"Tokenized short-term Treasury fund",
    manager:"BlackRock",
    tokenizationPlatform:"Securitize",
    exposure:"Cash, U.S. Treasury bills and repurchase agreements",
    access:"Qualified investors",
    networks:["Ethereum","Aptos","Arbitrum","Avalanche","Optimism","Polygon","Solana","BNB Chain","Tempo"],
    status:"Active",
    summary:"BlackRock's flagship tokenized short-term Treasury fund, using public blockchain rails for eligible investor access and transfer.",
    primarySource:"https://investors.securitize.io/news/news-details/2026/Tempo-expands-onchain-yield-offering-with-BlackRocks-BUIDL-fund/default.aspx",
    sourceLabel:"Securitize / Tempo deployment announcement",
    asOf:"2026-07-30"
  }
];

export const assetBySlug = (slug:string) => assets.find(a => a.slug === slug);
