declare module 'astro:content' {
	interface Render {
		'.mdx': Promise<{
			Content: import('astro').MarkdownInstance<{}>['Content'];
			headings: import('astro').MarkdownHeading[];
			remarkPluginFrontmatter: Record<string, any>;
			components: import('astro').MDXInstance<{}>['components'];
		}>;
	}
}

declare module 'astro:content' {
	interface RenderResult {
		Content: import('astro/runtime/server/index.js').AstroComponentFactory;
		headings: import('astro').MarkdownHeading[];
		remarkPluginFrontmatter: Record<string, any>;
	}
	interface Render {
		'.md': Promise<RenderResult>;
	}

	export interface RenderedContent {
		html: string;
		metadata?: {
			imagePaths: Array<string>;
			[key: string]: unknown;
		};
	}
}

declare module 'astro:content' {
	type Flatten<T> = T extends { [K: string]: infer U } ? U : never;

	export type CollectionKey = keyof AnyEntryMap;
	export type CollectionEntry<C extends CollectionKey> = Flatten<AnyEntryMap[C]>;

	export type ContentCollectionKey = keyof ContentEntryMap;
	export type DataCollectionKey = keyof DataEntryMap;

	type AllValuesOf<T> = T extends any ? T[keyof T] : never;
	type ValidContentEntrySlug<C extends keyof ContentEntryMap> = AllValuesOf<
		ContentEntryMap[C]
	>['slug'];

	/** @deprecated Use `getEntry` instead. */
	export function getEntryBySlug<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(
		collection: C,
		// Note that this has to accept a regular string too, for SSR
		entrySlug: E,
	): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;

	/** @deprecated Use `getEntry` instead. */
	export function getDataEntryById<C extends keyof DataEntryMap, E extends keyof DataEntryMap[C]>(
		collection: C,
		entryId: E,
	): Promise<CollectionEntry<C>>;

	export function getCollection<C extends keyof AnyEntryMap, E extends CollectionEntry<C>>(
		collection: C,
		filter?: (entry: CollectionEntry<C>) => entry is E,
	): Promise<E[]>;
	export function getCollection<C extends keyof AnyEntryMap>(
		collection: C,
		filter?: (entry: CollectionEntry<C>) => unknown,
	): Promise<CollectionEntry<C>[]>;

	export function getEntry<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(entry: {
		collection: C;
		slug: E;
	}): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof DataEntryMap,
		E extends keyof DataEntryMap[C] | (string & {}),
	>(entry: {
		collection: C;
		id: E;
	}): E extends keyof DataEntryMap[C]
		? Promise<DataEntryMap[C][E]>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(
		collection: C,
		slug: E,
	): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof DataEntryMap,
		E extends keyof DataEntryMap[C] | (string & {}),
	>(
		collection: C,
		id: E,
	): E extends keyof DataEntryMap[C]
		? Promise<DataEntryMap[C][E]>
		: Promise<CollectionEntry<C> | undefined>;

	/** Resolve an array of entry references from the same collection */
	export function getEntries<C extends keyof ContentEntryMap>(
		entries: {
			collection: C;
			slug: ValidContentEntrySlug<C>;
		}[],
	): Promise<CollectionEntry<C>[]>;
	export function getEntries<C extends keyof DataEntryMap>(
		entries: {
			collection: C;
			id: keyof DataEntryMap[C];
		}[],
	): Promise<CollectionEntry<C>[]>;

	export function render<C extends keyof AnyEntryMap>(
		entry: AnyEntryMap[C][string],
	): Promise<RenderResult>;

	export function reference<C extends keyof AnyEntryMap>(
		collection: C,
	): import('astro/zod').ZodEffects<
		import('astro/zod').ZodString,
		C extends keyof ContentEntryMap
			? {
					collection: C;
					slug: ValidContentEntrySlug<C>;
				}
			: {
					collection: C;
					id: keyof DataEntryMap[C];
				}
	>;
	// Allow generic `string` to avoid excessive type errors in the config
	// if `dev` is not running to update as you edit.
	// Invalid collection names will be caught at build time.
	export function reference<C extends string>(
		collection: C,
	): import('astro/zod').ZodEffects<import('astro/zod').ZodString, never>;

	type ReturnTypeOrOriginal<T> = T extends (...args: any[]) => infer R ? R : T;
	type InferEntrySchema<C extends keyof AnyEntryMap> = import('astro/zod').infer<
		ReturnTypeOrOriginal<Required<ContentConfig['collections'][C]>['schema']>
	>;

	type ContentEntryMap = {
		"articles": {
"ark-invest-tokenizes-ark-venture-fund-through-securitize.mdx": {
	id: "ark-invest-tokenizes-ark-venture-fund-through-securitize.mdx";
  slug: "ark-invest-tokenizes-ark-venture-fund-through-securitize";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"avalanche-is-pulling-ahead-in-tokenized-stocks.mdx": {
	id: "avalanche-is-pulling-ahead-in-tokenized-stocks.mdx";
  slug: "avalanche-is-pulling-ahead-in-tokenized-stocks";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"backed-explained.mdx": {
	id: "backed-explained.mdx";
  slug: "backed-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"bybit-adds-franklin-templeton-tokenized-funds-as-off-exchange-collateral.mdx": {
	id: "bybit-adds-franklin-templeton-tokenized-funds-as-off-exchange-collateral.mdx";
  slug: "bybit-adds-franklin-templeton-tokenized-funds-as-off-exchange-collateral";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"canada-six-banks-tokenized-deposits.mdx": {
	id: "canada-six-banks-tokenized-deposits.mdx";
  slug: "canada-six-banks-tokenized-deposits";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"cbdcs-vs-stablecoins.mdx": {
	id: "cbdcs-vs-stablecoins.mdx";
  slug: "cbdcs-vs-stablecoins";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"centrifuge-explained.mdx": {
	id: "centrifuge-explained.mdx";
  slug: "centrifuge-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"chainlink-and-tokenization-explained.mdx": {
	id: "chainlink-and-tokenization-explained.mdx";
  slug: "chainlink-and-tokenization-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"ethereum-and-the-tokenized-economy.mdx": {
	id: "ethereum-and-the-tokenized-economy.mdx";
  slug: "ethereum-and-the-tokenized-economy";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"figure-explained.mdx": {
	id: "figure-explained.mdx";
  slug: "figure-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"franklin-templeton-turns-686m-tokenized-fund-shares-into-bybit-collateral.mdx": {
	id: "franklin-templeton-turns-686m-tokenized-fund-shares-into-bybit-collateral.mdx";
  slug: "franklin-templeton-turns-686m-tokenized-fund-shares-into-bybit-collateral";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"goldfinch-explained.mdx": {
	id: "goldfinch-explained.mdx";
  slug: "goldfinch-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"how-does-asset-tokenization-work.mdx": {
	id: "how-does-asset-tokenization-work.mdx";
  slug: "how-does-asset-tokenization-work";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"kakao-pay-securities-eyes-global-push-with-tokenized-stocks.mdx": {
	id: "kakao-pay-securities-eyes-global-push-with-tokenized-stocks.mdx";
  slug: "kakao-pay-securities-eyes-global-push-with-tokenized-stocks";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"maple-finance-explained.mdx": {
	id: "maple-finance-explained.mdx";
  slug: "maple-finance-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"ondo-finance-explained.mdx": {
	id: "ondo-finance-explained.mdx";
  slug: "ondo-finance-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"oracle-ibm-cosmos-build-routes-into-swift-s-ledger-as-vendors-bet-on-tokenized-deposits.mdx": {
	id: "oracle-ibm-cosmos-build-routes-into-swift-s-ledger-as-vendors-bet-on-tokenized-deposits.mdx";
  slug: "oracle-ibm-cosmos-build-routes-into-swift-s-ledger-as-vendors-bet-on-tokenized-deposits";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"plume-network-explained.mdx": {
	id: "plume-network-explained.mdx";
  slug: "plume-network-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"polymesh-explained.mdx": {
	id: "polymesh-explained.mdx";
  slug: "polymesh-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"quant-network-explained.mdx": {
	id: "quant-network-explained.mdx";
  slug: "quant-network-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"real-world-assets-on-injective-how-do-tokenized-stocks-and-commodities-actually-work-onchain.mdx": {
	id: "real-world-assets-on-injective-how-do-tokenized-stocks-and-commodities-actually-work-onchain.mdx";
  slug: "real-world-assets-on-injective-how-do-tokenized-stocks-and-commodities-actually-work-onchain";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"rwa-infrastructure-explained.mdx": {
	id: "rwa-infrastructure-explained.mdx";
  slug: "rwa-infrastructure-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"securitize-explained.mdx": {
	id: "securitize-explained.mdx";
  slug: "securitize-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"september-2026-global-regulatory-brief-token-securities-stablecoins-and-tokenized-bonds.mdx": {
	id: "september-2026-global-regulatory-brief-token-securities-stablecoins-and-tokenized-bonds.mdx";
  slug: "september-2026-global-regulatory-brief-token-securities-stablecoins-and-tokenized-bonds";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"stablecoin-market-structure-shifts.mdx": {
	id: "stablecoin-market-structure-shifts.mdx";
  slug: "stablecoin-market-structure-shifts";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"stablecoins-explained.mdx": {
	id: "stablecoins-explained.mdx";
  slug: "stablecoins-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"stablecoins-vs-tokenized-deposits.mdx": {
	id: "stablecoins-vs-tokenized-deposits.mdx";
  slug: "stablecoins-vs-tokenized-deposits";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"superstate-explained.mdx": {
	id: "superstate-explained.mdx";
  slug: "superstate-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"the-clearing-house-quant-on-chain-money.mdx": {
	id: "the-clearing-house-quant-on-chain-money.mdx";
  slug: "the-clearing-house-quant-on-chain-money";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"the-companies-building-tokenized-finance.mdx": {
	id: "the-companies-building-tokenized-finance.mdx";
  slug: "the-companies-building-tokenized-finance";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-assets-vs-traditional-assets.mdx": {
	id: "tokenized-assets-vs-traditional-assets.mdx";
  slug: "tokenized-assets-vs-traditional-assets";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-bonds-explained.mdx": {
	id: "tokenized-bonds-explained.mdx";
  slug: "tokenized-bonds-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-funds-explained.mdx": {
	id: "tokenized-funds-explained.mdx";
  slug: "tokenized-funds-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-real-estate-explained.mdx": {
	id: "tokenized-real-estate-explained.mdx";
  slug: "tokenized-real-estate-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-stocks-explained.mdx": {
	id: "tokenized-stocks-explained.mdx";
  slug: "tokenized-stocks-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-stocks-just-did-20-9-billion-in-dex-trading-in-30-days.mdx": {
	id: "tokenized-stocks-just-did-20-9-billion-in-dex-trading-in-30-days.mdx";
  slug: "tokenized-stocks-just-did-20-9-billion-in-dex-trading-in-30-days";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-treasuries-explained.mdx": {
	id: "tokenized-treasuries-explained.mdx";
  slug: "tokenized-treasuries-explained";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"tokenized-treasuries-market-update.mdx": {
	id: "tokenized-treasuries-market-update.mdx";
  slug: "tokenized-treasuries-market-update";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"uk-banks-live-tokenised-sterling-deposits.mdx": {
	id: "uk-banks-live-tokenised-sterling-deposits.mdx";
  slug: "uk-banks-live-tokenised-sterling-deposits";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"united-states-oil-tokenized-fund-ondo-price-usoon-usd-today-live-price-market-cap-chart.mdx": {
	id: "united-states-oil-tokenized-fund-ondo-price-usoon-usd-today-live-price-market-cap-chart.mdx";
  slug: "united-states-oil-tokenized-fund-ondo-price-usoon-usd-today-live-price-market-cap-chart";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"what-are-real-world-assets.mdx": {
	id: "what-are-real-world-assets.mdx";
  slug: "what-are-real-world-assets";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"what-is-onchain-settlement.mdx": {
	id: "what-is-onchain-settlement.mdx";
  slug: "what-is-onchain-settlement";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"what-is-programmable-money.mdx": {
	id: "what-is-programmable-money.mdx";
  slug: "what-is-programmable-money";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"what-is-tokenization.mdx": {
	id: "what-is-tokenization.mdx";
  slug: "what-is-tokenization";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
"why-are-financial-assets-moving-onchain.mdx": {
	id: "why-are-financial-assets-moving-onchain.mdx";
  slug: "why-are-financial-assets-moving-onchain";
  body: string;
  collection: "articles";
  data: InferEntrySchema<"articles">
} & { render(): Render[".mdx"] };
};

	};

	type DataEntryMap = {
		
	};

	type AnyEntryMap = ContentEntryMap & DataEntryMap;

	export type ContentConfig = typeof import("../../src/content/config.js");
}
