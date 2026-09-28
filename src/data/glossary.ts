export interface GlossaryTerm {
  slug: string;
  term: string;
  short: string;
  definition: string;
  example?: string;
}

export const glossary: GlossaryTerm[] = [
  { slug:"rwa", term:"RWA", short:"Real-world asset", definition:"A financial or physical asset whose ownership, cash flows or economic exposure is represented or managed using blockchain infrastructure.", example:"Government bonds, private credit and funds can all be represented onchain." },
  { slug:"tokenization", term:"Tokenization", short:"Putting asset rights on blockchain rails", definition:"The process of representing ownership, claims or economic rights to an asset with blockchain-based records or tokens." },
  { slug:"onchain", term:"Onchain", short:"Recorded on a blockchain", definition:"Activity whose transactions or ownership records are written to blockchain infrastructure rather than existing only in conventional databases." },
  { slug:"tokenized-deposit", term:"Tokenized deposit", short:"Bank deposit represented as a token", definition:"A digital representation of commercial bank money. Unlike a typical stablecoin, the claim remains a deposit liability of the issuing bank." },
  { slug:"settlement", term:"Settlement", short:"The final exchange of money and assets", definition:"The stage when a financial transaction becomes final and the buyer receives the asset while the seller receives payment." },
  { slug:"transfer-agent", term:"Transfer agent", short:"Official ownership-record administrator", definition:"An entity responsible for maintaining investor ownership records and supporting transfers, issuance and other administrative functions for securities." },
  { slug:"blockchain-rails", term:"Blockchain rails", short:"The network layer transactions run on", definition:"A shorthand for blockchain infrastructure used to issue, transfer, settle or record tokenized assets." },
  { slug:"private-credit", term:"Private credit", short:"Loans made outside public bond markets", definition:"Debt financing negotiated privately between borrowers and lenders or investment funds rather than issued as publicly traded bonds." },
  { slug:"money-market-fund", term:"Money market fund", short:"Fund focused on short-term liquid debt", definition:"A fund that invests in highly liquid short-term instruments such as government securities, cash and repurchase agreements." },
  { slug:"smart-contract", term:"Smart contract", short:"Blockchain-based programmable logic", definition:"Code deployed on a blockchain that can execute predefined rules for transactions, assets or applications." },
];

export const glossaryBySlug=(slug:string)=>glossary.find(x=>x.slug===slug);
