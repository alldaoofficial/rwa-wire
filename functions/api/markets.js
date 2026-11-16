/**
 * RWA Wire market snapshot endpoint.
 * Uses the deployed market cache, not an unbounded client-side provider request.
 * Each response includes explicit freshness metadata; this is not a streaming feed.
 */
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const source = new URL("/data/markets.json", url.origin);
  let response;
  try {
    response = await env.ASSETS.fetch(new Request(source.toString(), { method: "GET" }));
  } catch {
    return Response.json({ error: "Market snapshot unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
  if (!response.ok) {
    return Response.json({ error: "Market snapshot unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
  try {
    const data = await response.json();
    const fetchedAt = Date.parse(data.fetchedAt || "");
    const ageMinutes = Number.isFinite(fetchedAt) && fetchedAt <= Date.now() ? Math.floor((Date.now() - fetchedAt) / 60000) : null;
    return Response.json({
      ...data,
      freshness: {
        ageMinutes,
        delayed: ageMinutes === null || ageMinutes > 120,
        kind: "cached-provider-snapshot"
      }
    }, { headers: { "Cache-Control": "public, max-age=60", "Access-Control-Allow-Origin": "*" } });
  } catch {
    return Response.json({ error: "Invalid market snapshot" }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
