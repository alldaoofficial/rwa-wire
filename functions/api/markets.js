/**
 * RWA Wire market quotes. CoinGecko first, CoinPaprika verified-identity
 * fallback. Successful provider responses are edge-cached for 60 seconds.
 * The deployed JSON is an explicitly delayed last resort, never "live".
 */
const universe = {
  "chainlink":["LINK","Chainlink"],"ondo-finance":["ONDO","Ondo"],
  "maple-finance":["SYRUP","Maple Finance"],"zebec-protocol":["ZBCN","Zebec Network"],
  "plume":["PLUME","Plume"],"centrifuge":["CFG","Centrifuge"],
  "polymesh":["POLYX","Polymesh"],"goldfinch":["GFI","Goldfinch"],
  "clearpool":["CPOOL","Clearpool"],"mantra-dao":["MANTRA","MANTRA"],
  "reserve-rights-token":["RSR","Reserve Rights"],"origintrail":["TRAC","OriginTrail"],
  "origin-protocol":["OGN","Origin Protocol"],"truefi":["TRU","TrueFi"],
  "polytrade":["TRADE","Polytrade"],"propchain":["PROPC","Propchain"],
  "realio-network":["RIO","Realio Network"],"dusk-network":["DUSK","Dusk"],
  "chex-token":["CHEX","Chintai"],"landshare":["LAND","Landshare"],
  "boson-protocol":["BOSON","Boson Protocol"],"stobox-token":["STBU","Stobox"],
  "brickken":["BKN","Brickken"],"parcl":["PRCL","Parcl"],
  "tokenfi":["TOKEN","TokenFi"],"ix-swap":["IXS","IX Swap"]
};
const aliases={"maple-finance":"syrup","zebec-protocol":"zebec-network","mantra-dao":"mantra"};
const maxAgeMs=2*60*60*1000;
const keys=Object.keys(universe);
function valid(q,now){
  const ts=Number(q?.last_updated_at)*1000;
  return typeof q?.usd==="number"&&Number.isFinite(q.usd)&&q.usd>0&&
    Number.isFinite(ts)&&ts>0&&ts<=now&&now-ts<=maxAgeMs;
}
function stamp(iso){const n=Date.parse(iso);return Number.isFinite(n)?n:null;}
function response(payload,age=60){
  return Response.json(payload,{headers:{"Cache-Control":`public, max-age=${age}`,"Access-Control-Allow-Origin":"*"}});
}
async function coingecko(env,now){
  const ids=keys.map(k=>aliases[k]||k);
  const url="https://api.coingecko.com/api/v3/simple/price?ids="+ids.join(",")+
    "&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true";
  const headers={Accept:"application/json"};
  if(env.COINGECKO_API_KEY)headers["x-cg-demo-api-key"]=env.COINGECKO_API_KEY;
  const res=await fetch(url,{headers,signal:AbortSignal.timeout(9000)});
  if(!res.ok)throw Error("CoinGecko HTTP "+res.status);
  const data=await res.json();
  const found={};
  for(const key of keys){
    // Legacy CPOOL cannot be inferred from CoinGecko's migrated CLEAR identity.
    if(key==="clearpool")continue;
    const q=data[aliases[key]||key];
    if(valid(q,now))found[key]=q;
  }
  return found;
}
async function coinpaprika(now){
  const res=await fetch("https://api.coinpaprika.com/v1/tickers?quotes=USD",{
    headers:{Accept:"application/json"},signal:AbortSignal.timeout(13000)
  });
  if(!res.ok)throw Error("CoinPaprika HTTP "+res.status);
  const tickers=await res.json();
  if(!Array.isArray(tickers))throw Error("CoinPaprika invalid response");
  const result={};
  for(const [key,[symbol,name]] of Object.entries(universe)){
    const candidates=tickers.filter(t=>String(t?.symbol||"").toUpperCase()===symbol.toUpperCase()&&String(t?.name||"").toLowerCase()===name.toLowerCase());
    if(candidates.length!==1)continue;
    const t=candidates[0],q=t.quotes?.USD||{},updated=stamp(t.last_updated);
    const quote={usd:q.price,usd_market_cap:q.market_cap,usd_24h_vol:q.volume_24h,
      usd_24h_change:q.percent_change_24h,last_updated_at:updated===null?null:Math.floor(updated/1000)};
    if(valid(quote,now))result[key]=quote;
  }
  return result;
}
export async function onRequestGet({request,env}){
  const now=Date.now(),url=new URL(request.url);
  const cacheKey=new Request(new URL("/api/markets",url.origin).toString());
  const cache=caches.default,hit=await cache.match(cacheKey);
  if(hit)return hit;
  let assets={},sources=[],errors=[],fetchedAt=new Date(now).toISOString();
  try{
    const cg=await coingecko(env,now);
    Object.assign(assets,cg);
    if(Object.keys(cg).length)sources.push("CoinGecko");
  }catch(error){errors.push(error instanceof Error?error.message:"CoinGecko request failed");}
  if(Object.keys(assets).length<keys.length-1){
    try{
      const cp=await coinpaprika(now);
      let added=0;
      for(const [key,quote] of Object.entries(cp)){
        if(!assets[key]){assets[key]=quote;added++;}
      }
      if(added)sources.push("CoinPaprika");
    }catch(error){errors.push(error instanceof Error?error.message:"CoinPaprika request failed");}
  }
  const providerCount=Object.keys(assets).length;
  let fallback=false;
  if(!providerCount){
    fallback=true;
    try{
      const res=await env.ASSETS.fetch(new Request(new URL("/data/markets.json",url.origin)));
      if(!res.ok)throw Error("Snapshot unavailable");
      const snapshot=await res.json();
      assets=snapshot.assets||{};
      delete assets.clearpool;
      fetchedAt=snapshot.fetchedAt||null;
    }catch{
      return Response.json({error:"Market quotes unavailable",providerStatus:errors.join("; ")},{status:503,headers:{"Cache-Control":"no-store"}});
    }
  }
  const age=fetchedAt?stamp(fetchedAt):null;
  const ageMinutes=age===null?null:Math.max(0,Math.floor((now-age)/60000));
  const source=fallback?"Cached provider snapshot (fallback)":sources.join(" + ");
  const payload={source,fetchedAt,assets,coverage:{available:Object.keys(assets).length,tracked:keys.length},
    ...(errors.length?{providerStatus:errors.join("; ")}:{}),
    freshness:{ageMinutes,delayed:fallback||ageMinutes===null||ageMinutes>2,
      kind:fallback?"cached-provider-snapshot":"provider-polled-quotes"}};
  const result=response(payload,fallback?15:60);
  if(!fallback)await cache.put(cacheKey,result.clone());
  return result;
}
