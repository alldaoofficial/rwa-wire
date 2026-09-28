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
  },
  {
    slug:"benji",
    name:"BENJI",
    fullName:"Franklin OnChain U.S. Government Money Fund (FOBXX)",
    assetClass:"Tokenized U.S. government money market fund",
    manager:"Franklin Templeton",
    tokenizationPlatform:"Benji Technology Platform",
    exposure:"Government securities, cash and repurchase agreements",
    access:"Retail and institutional access varies by market and channel",
    networks:["Stellar","Public blockchain infrastructure"],
    status:"Active",
    summary:"Franklin Templeton's onchain money market fund uses its Benji platform for blockchain-integrated share ownership and transaction recordkeeping.",
    primarySource:"https://www.franklintempleton.com/press-releases/news-room/2026/franklin-templeton-stellar-development-foundation-mark-five-years-of-benji-the-first-u.s.-registered-tokenized-money-market-fund",
    sourceLabel:"Franklin Templeton five-year BENJI announcement",
    asOf:"2026-04-30"
  },
  {
    slug:"jpm-coin",
    name:"JPM Coin",
    fullName:"J.P. Morgan USD-denominated deposit token",
    assetClass:"Tokenized commercial bank deposit",
    manager:"J.P. Morgan",
    tokenizationPlatform:"Kinexys by J.P. Morgan",
    exposure:"USD commercial bank deposits at J.P. Morgan",
    access:"J.P. Morgan institutional clients",
    networks:["Base"],
    status:"Active",
    summary:"A bank-issued USD deposit token for institutional clients, designed for programmable movement, collateral and settlement on public blockchain rails.",
    primarySource:"https://www.jpmorgan.com/kinexys/jpm-coin",
    sourceLabel:"J.P. Morgan JPM Coin product page",
    asOf:"2026-04-28"
  }
];

export const assetBySlug = (slug:string) => assets.find(a => a.slug === slug);
