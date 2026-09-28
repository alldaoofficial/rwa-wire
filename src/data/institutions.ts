export interface Institution {
  slug: string;
  name: string;
  type: string;
  role: string;
  focus: string[];
  networks: string[];
  status: "Active" | "Monitoring";
}

export const institutions: Institution[] = [
  { slug:"blackrock", name:"BlackRock", type:"Asset manager", role:"Institutional asset management and tokenized-fund participation", focus:["Tokenized funds","Digital assets","Institutional markets"], networks:["Ethereum"], status:"Active" },
  { slug:"jpmorgan", name:"JPMorgan", type:"Bank", role:"Banking, payments and institutional digital-asset infrastructure", focus:["Payments","Tokenized deposits","Institutional settlement"], networks:["Institutional blockchain infrastructure"], status:"Active" },
  { slug:"dtcc", name:"DTCC", type:"Market infrastructure", role:"Post-trade market infrastructure and financial-market modernization", focus:["Settlement","Tokenization","Capital markets"], networks:["Institutional market infrastructure"], status:"Active" },
  { slug:"securitize", name:"Securitize", type:"Tokenization platform", role:"Issuance and servicing infrastructure for tokenized securities", focus:["Tokenized securities","Funds","Transfer agency"], networks:["Ethereum","Multi-chain"], status:"Active" },
  { slug:"franklin-templeton", name:"Franklin Templeton", type:"Asset manager", role:"Asset management with blockchain-enabled investment products", focus:["Tokenized funds","Government securities","Digital assets"], networks:["Multi-chain"], status:"Active" },
];

export const institutionBySlug = (slug: string) => institutions.find((i) => i.slug === slug);
