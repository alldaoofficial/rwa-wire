const allowedEvents = new Set([
  "social_landing","affiliate_click","bitunix_guide_click","placement_click","x_click",
  "newsletter_submit","newsletter_pending","newsletter_error","newsletter_confirmed","newsletter_unsubscribed",
  "telegram_click","topic_click","project_click","search","search_zero_results",
  "search_result_click","market_click","market_asset_click","content_click"
]);
const allowedOrigins = new Set(["https://therwawire.com","https://www.therwawire.com"]);
function cors(origin: string) {
  return {
    "Access-Control-Allow-Origin": allowedOrigins.has(origin) ? origin : "https://therwawire.com",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}
Deno.serve(async (req: Request) => {
  const origin=req.headers.get("origin")||"";
  const headers=cors(origin);
  if (req.method === "OPTIONS") {
    if (!allowedOrigins.has(origin)) return new Response(null,{status:403,headers});
    return new Response(null,{status:204,headers});
  }
  if (req.method !== "POST") return new Response("Method not allowed",{status:405,headers});
  if (!allowedOrigins.has(origin)) return new Response("Forbidden",{status:403,headers});
  try {
    const body=await req.json();
    const event=String(body.event||"").slice(0,64);
    if (!allowedEvents.has(event)) return new Response("Invalid event",{status:400,headers});
    const m=body.metadata && typeof body.metadata === 'object' && !Array.isArray(body.metadata) ? {...body.metadata} : {};
    const source=m.source, campaign=m.campaign;
    delete m.source; delete m.campaign;
    const validSource=['x','telegram'].includes(source) && typeof campaign==='string' && /^[a-z0-9_-]{1,160}$/.test(campaign);
    if(event==='social_landing'&&!validSource)return new Response('Invalid attribution',{status:400,headers});
    if(validSource){m.source=source;m.campaign=campaign;}
    const row={
      event,
      path:String(body.path||"").slice(0,500),
      target:String(body.target||"").slice(0,500),
      referrer:String(body.referrer||"").slice(0,255),
      metadata:m,
      user_agent:String(req.headers.get("user-agent")||"").slice(0,500),
    };
    const url=Deno.env.get("SUPABASE_URL")!+"/rest/v1/growth_events";
    const key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const r=await fetch(url,{method:"POST",headers:{"apikey":key,"authorization":`Bearer ${key}`,"content-type":"application/json","prefer":"return=minimal"},body:JSON.stringify(row)});
    if(!r.ok) return new Response("Storage error",{status:500,headers});
    return new Response(null,{status:204,headers});
  } catch { return new Response("Bad request",{status:400,headers}); }
});
