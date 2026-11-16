/**
 * Shared near-real-time quote endpoint for RWA Wire.
 * CoinGecko responses are cached at the edge for 60 seconds. On failure, the
 * deployed snapshot remains available, explicitly marked as fallback.
 * Quotes are never described as exchange-streaming or tick-by-tick.
 */
const aliases = { "maple-finance": "syrup", "zebec-protocol": "zebec-network", "mantra-dao": "mantra" };
const ids = ["chainlink","ondo-finance","maple-finance","zebec-protocol","plume","centrifuge","polymesh","goldfinch","clearpool","mantra-dao","reserve-rights-token","origintrail","origin-protocol","truefi","polytrade","propchain","realio-network","dusk-network","chex-token","landshare","boson-protocol","stobox-token","brickken","parcl","tokenfi","ix-swap"];
const MAX_AGE_MS = 120 * 60 * 1000;
function valid(q, now) {
  if (!q || typeof q.usd !== "number" || !Number.isFinite(q.usd) || q.usd <= 0) return false;
  const timestamp = q.last_updated_at * 1000;
  return Number.isFinite(timestamp) && timestamp > 0 && timestamp <= now && now - timestamp <= MAX_AGE_MS;
}
function response(data, maxAge = 30) {
  return Response.json(data, { headers: { "Cache-Control": `public, max-age=${maxAge}`, "Access-Control-Allow-Origin": "*" } });
}
export async function onRequestGet({ request, env }) {
  const now = Date.now();
  const url = new URL(request.url);
  const cacheKey = new Request(new URL("/api/markets", url.origin).toString());
  const edgeCache = caches.default;
  const hit = await edgeCache.match(cacheKey);
  if (hit) return hit;
  let assets = {};
  let source = "CoinGecko";
  let fetchedAt = new Date(now).toISOString();
  try {
    const providerIds = ids.map(id => aliases[id] || id);
    const providerUrl = "https://api.coingecko.com/api/v3/simple/price?ids=" + providerIds.join(",") + "&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true";
    const headers = { Accept: "application/json" };
    if (env.COINGECKO_API_KEY) headers["x-cg-demo-api-key"] = env.COINGECKO_API_KEY;
    const upstream = await fetch(providerUrl, { headers, signal: AbortSignal.timeout(7000) });
    if (!upstream.ok) throw new Error("Quote provider unavailable");
    const quotes = await upstream.json();
    for (const id of ids) {
      // CoinGecko's clearpool ID now resolves to CLEAR, not the legacy CPOOL
      // ticker. Do not silently label the migrated asset as CPOOL.
      if (id === "clearpool") continue;
      const q = quotes[aliases[id] || id];
      if (valid(q, now)) assets[id] = q;
    }
    if (Object.keys(assets).length < 4) throw new Error("Insufficient fresh quotes");
  } catch {
    source = "Cached provider snapshot (fallback)";
    try {
      const snapshot = await env.ASSETS.fetch(new Request(new URL("/data/markets.json", url.origin)));
      if (!snapshot.ok) throw new Error("Snapshot missing");
      const data = await snapshot.json();
      assets = data.assets || {};
      // Never expose the unverified legacy CPOOL identity as a live quote.
      delete assets.clearpool;
      fetchedAt = data.fetchedAt || null;
    } catch {
      return Response.json({ error: "Market quotes unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
    }
  }
  const ageMinutes = fetchedAt ? Math.max(0, Math.floor((now - Date.parse(fetchedAt)) / 60000)) : null;
  const payload = { source, fetchedAt, assets, freshness: { ageMinutes, delayed: source.includes("fallback") || ageMinutes === null || ageMinutes > 2, kind: source === "CoinGecko" ? "provider-polled-quotes" : "cached-provider-snapshot" } };
  const result = response(payload, 60);
  if (source === "CoinGecko") await edgeCache.put(cacheKey, result.clone());
  return result;
}
