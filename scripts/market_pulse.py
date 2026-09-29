#!/usr/bin/env python3
"""Generate a factual RWA Wire Market Pulse from the shared market cache.

V2 remains dry-run only. It separates Telegram and X copy, adds prices,
liquidity context, breadth and deterministic market reads without inventing causes.
"""
import json, pathlib, statistics
from datetime import datetime, timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
src=ROOT/"public/data/markets.json"
if not src.exists(): raise SystemExit("public/data/markets.json missing")
d=json.loads(src.read_text(encoding="utf-8")); assets=d.get("assets") or {}
meta={"chainlink":("LINK","Chainlink"),"ondo-finance":("ONDO","Ondo"),"maple-finance":("SYRUP","Maple"),"zebec-protocol":("ZBCN","Zebec"),"plume":("PLUME","Plume"),"centrifuge":("CFG","Centrifuge"),"polymesh":("POLYX","Polymesh"),"goldfinch":("GFI","Goldfinch"),"clearpool":("CPOOL","Clearpool"),"mantra-dao":("OM","MANTRA")}
rows=[]
for key,v in assets.items():
 if key not in meta or not isinstance(v,dict): continue
 change=v.get("usd_24h_change"); price=v.get("usd"); vol=v.get("usd_24h_vol")
 if not isinstance(change,(int,float)) or not isinstance(price,(int,float)): continue
 sym,name=meta[key]; rows.append({"id":key,"symbol":sym,"name":name,"price":price,"change24h":change,"volume24h":vol if isinstance(vol,(int,float)) else None})
if len(rows)<4: raise SystemExit(f"Only {len(rows)} usable RWA assets; refusing to generate pulse")
rows.sort(key=lambda x:x["change24h"],reverse=True)
changes=[x["change24h"] for x in rows]; avg=sum(changes)/len(changes); median=statistics.median(changes)
up=sum(x>0 for x in changes); down=sum(x<0 for x in changes); flat=len(rows)-up-down
leader=rows[0]; weakest=rows[-1]; liquid=max((x for x in rows if x["volume24h"] is not None),key=lambda x:x["volume24h"],default=None)
if up/len(rows)>=.75: tone="broadly higher"
elif down/len(rows)>=.75: tone="broadly lower"
else: tone="mixed"
def pct(x): return f"{x:+.1f}%"
def price(x):
 p=x["price"]
 return f"${p:,.4f}" if p<1 else f"${p:,.2f}"
def money(x):
 if x is None:return "n/a"
 if x>=1e9:return f"${x/1e9:.1f}B"
 if x>=1e6:return f"${x/1e6:.1f}M"
 if x>=1e3:return f"${x/1e3:.1f}K"
 return f"${x:,.0f}"
def line(x): return f"{'▲' if x['change24h']>0 else '▼' if x['change24h']<0 else '•'} {x['symbol']} {pct(x['change24h'])} · {price(x)}"
# Relative labels avoid calling a positive asset a loser during an all-green session.
top_label="Top movers"; low_label="Lower movers" if weakest["change24h"]>=0 else "Weakest movers"
market_read=[]
market_read.append(f"Breadth is {'strong' if up/len(rows)>=.75 else 'weak' if down/len(rows)>=.75 else 'split'} with {up}/{len(rows)} tracked assets positive.")
if abs(leader["change24h"])>=10: market_read.append(f"{leader['symbol']} is the standout move at {pct(leader['change24h'])}.")
spread=leader["change24h"]-weakest["change24h"]
if spread>=10: market_read.append(f"Dispersion is elevated: {spread:.1f} percentage points separate the strongest and weakest tracked assets.")
if liquid: market_read.append(f"{liquid['symbol']} has the highest reported 24h volume in the tracked basket at {money(liquid['volume24h'])}.")
read=" ".join(market_read[:3])
telegram=(f"RWA WIRE // MARKET PULSE\n\nTracked RWA tokens are {tone} over 24h.\n"
 f"Breadth: {up} up / {down} down"+(f" / {flat} flat" if flat else "")+f"\nBasket: avg {pct(avg)} · median {pct(median)}\n\n"
 f"{top_label}\n"+"\n".join(line(x) for x in rows[:3])+f"\n\n{low_label}\n"+"\n".join(line(x) for x in rows[-3:])+f"\n\nMARKET READ\n{read}\n\nData: {d.get('source','market provider')} · 24h change")
# X stays deliberately compact and native; no article URL exists for dry-run pulses.
x=(f"RWA WIRE // MARKET PULSE\n\nRWA basket: {pct(avg)} avg · {up}/{len(rows)} green\n"
   +" | ".join(f"{x['symbol']} {pct(x['change24h'])}" for x in rows[:3])
   +f"\n\n{read}\n\nData: {d.get('source','market provider')}")
if len(x)>280: x=x[:276].rstrip()+"…"
now=datetime.now(timezone.utc); stamp=now.strftime("%Y-%m-%dT%H:%M:%SZ")
out={"version":2,"generatedAt":stamp,"status":"dry_run","source":d.get("source"),"sourceFetchedAt":d.get("fetchedAt"),"assetCount":len(rows),"basket":{"average24h":avg,"median24h":median,"up":up,"down":down,"flat":flat,"spreadPctPoints":spread},"leader":leader,"weakest":weakest,"highestVolume":liquid,"marketRead":read,"assets":rows,"telegram":telegram,"x":x}
target=ROOT/"publish/market-pulse"/f"{now.strftime('%Y-%m-%dT%H%M%SZ')}.json";target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(telegram); print("\n--- X PREVIEW ---\n"+x); print(f"\nDry-run saved to {target.relative_to(ROOT)}")
