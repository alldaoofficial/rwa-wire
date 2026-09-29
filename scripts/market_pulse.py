#!/usr/bin/env python3
"""Generate a factual RWA Wire Market Pulse from the shared market cache.

V1 is deliberately dry-run only: it writes reviewable output but does not publish.
"""
import json, pathlib, statistics
from datetime import datetime, timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
src=ROOT/"public/data/markets.json"
if not src.exists(): raise SystemExit("public/data/markets.json missing")
d=json.loads(src.read_text(encoding="utf-8")); assets=d.get("assets") or {}
meta={
 "chainlink":("LINK","Chainlink"),"ondo-finance":("ONDO","Ondo"),"maple-finance":("SYRUP","Maple"),
 "zebec-protocol":("ZBCN","Zebec"),"plume":("PLUME","Plume"),"centrifuge":("CFG","Centrifuge"),
 "polymesh":("POLYX","Polymesh"),"goldfinch":("GFI","Goldfinch"),"clearpool":("CPOOL","Clearpool"),"mantra-dao":("OM","MANTRA")}
rows=[]
for key,v in assets.items():
 if key not in meta or not isinstance(v,dict): continue
 change=v.get("usd_24h_change"); price=v.get("usd"); vol=v.get("usd_24h_vol")
 if not isinstance(change,(int,float)) or not isinstance(price,(int,float)): continue
 sym,name=meta[key]; rows.append({"id":key,"symbol":sym,"name":name,"price":price,"change24h":change,"volume24h":vol})
if len(rows)<4: raise SystemExit(f"Only {len(rows)} usable RWA assets; refusing to generate pulse")
rows.sort(key=lambda x:x["change24h"],reverse=True)
changes=[x["change24h"] for x in rows]; avg=sum(changes)/len(changes); median=statistics.median(changes)
up=sum(x>0 for x in changes); down=sum(x<0 for x in changes)
leader=rows[0]; laggard=rows[-1]
if avg>=2: tone="broadly higher"
elif avg<=-2: tone="broadly lower"
else: tone="mixed"
def pct(x): return f"{x:+.1f}%"
def line(x): return f"{'▲' if x['change24h']>=0 else '▼'} {x['symbol']} {pct(x['change24h'])}"
leaders=" | ".join(line(x) for x in rows[:3]); laggards=" | ".join(line(x) for x in rows[-3:])
now=datetime.now(timezone.utc); stamp=now.strftime("%Y-%m-%dT%H:%M:%SZ")
text=(f"RWA WIRE // MARKET PULSE\n\nTracked RWA tokens are {tone} over 24h. "
      f"{up} of {len(rows)} are higher and {down} are lower.\n\nLeaders\n{leaders}\n\nLaggards\n{laggards}\n\n"
      f"Basket avg {pct(avg)} | median {pct(median)}\n\nData: {d.get('source','market provider')} • 24h change")
out={"generatedAt":stamp,"status":"dry_run","source":d.get("source"),"sourceFetchedAt":d.get("fetchedAt"),
     "assetCount":len(rows),"basket":{"average24h":avg,"median24h":median,"up":up,"down":down},
     "leader":leader,"laggard":laggard,"assets":rows,"telegram":text,"x":text}
target=ROOT/"publish/market-pulse"/f"{now.strftime('%Y-%m-%dT%H%M%SZ')}.json";target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(text); print(f"\nDry-run saved to {target.relative_to(ROOT)}")
