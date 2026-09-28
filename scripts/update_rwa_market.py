#!/usr/bin/env python3
import re, urllib.request, pathlib, datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"src/data/rwa-market.json"
URLS={"overview":"https://defillama.com/rwa","categories":"https://defillama.com/rwa/categories","chains":"https://defillama.com/rwa/chains"}

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 RWA-Wire/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r: return r.read().decode("utf-8","ignore")

def money(text,label):
    plain=re.sub(r"<[^>]+>"," ",text)
    plain=re.sub(r"\\s+"," ",plain)
    aliases={
      "Total RWA Active Mcap":["Total RWA Active Mcap","RWA Active AUM","Active Mcap","Active Market Cap"],
      "Total RWA Onchain Mcap":["Total RWA Onchain Mcap","RWA Onchain AUM","Onchain Mcap","Onchain Market Cap"],
      "DeFi Active TVL":["DeFi Active TVL","Active TVL"],
    }
    for key in aliases.get(label,[label]):
        m=re.search(re.escape(key)+r'.{0,800}?\\$\\s*([0-9.,]+)\\s*([bmk]?)',plain,re.I|re.S)
        if m: return "$"+m.group(1)+m.group(2).upper()
    raise ValueError("missing "+label)

def rows(text,names):
    out=[]
    for name in names:
        i=text.lower().find(name.lower())
        if i<0: continue
        chunk=re.sub(r"<[^>]+>"," ",text[i:i+1800])
        vals=re.findall(r'\$[0-9][0-9.,]*(?:[bmk])?',chunk,re.I)
        if vals: out.append([name,vals[0].upper(),vals[1].upper() if len(vals)>1 else "—"])
    return out

o,c,h=(get(URLS[k]) for k in ("overview","categories","chains"))
data={
 "updated":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "metrics":[
  ["RWA Active AUM",money(o,"Total RWA Active Mcap")],
  ["RWA Onchain AUM",money(o,"Total RWA Onchain Mcap")],
  ["DeFi Active TVL",money(o,"DeFi Active TVL")]],
 "categories":rows(c,["Bond & MMF Funds","Gold & Commodities","Private Credit","Stocks & Equities","Crypto Funds","Real Estate"]),
 "chains":rows(h,["Ethereum","BSC","Stellar","Solana","Avalanche","Arbitrum","Zksync_era","Kinesis"])
}
if len(data["categories"])<5 or len(data["chains"])<6: raise ValueError("validation failed")
OUT.parent.mkdir(parents=True,exist_ok=True)
import json
OUT.write_text(json.dumps(data,indent=2)+"\n")
print("updated",OUT)
