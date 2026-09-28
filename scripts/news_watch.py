#!/usr/bin/env python3
"""Scheduled discovery for RWA Wire.

Discovers timely RWA/tokenization stories from Google News RSS, scores them,
deduplicates against repository state and writes ONE conservative inbox brief.
The downstream candidate generator + private Telegram approval remain the gate.
"""
import html, json, pathlib, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/"publish/news-watch-state.json"
INBOX=ROOT/"publish/inbox"
QUERIES=[
  '"tokenized fund" OR "tokenized treasury" OR "tokenized securities" OR "tokenized stocks"',
  '"tokenized deposits" OR "deposit token" OR "tokenized money market" OR "onchain finance"',
  '"real world assets" tokenization institution OR bank OR fund OR securities',
  'BlackRock OR Franklin Templeton OR JPMorgan OR DTCC tokenized OR tokenization OR onchain',
  'Securitize OR Ondo OR Centrifuge OR Chainlink "real world assets" OR tokenization',
  '"tokenized private credit" OR "tokenized bonds" OR "digital bonds" OR "tokenized real estate"',
  'stablecoin bank settlement institution tokenized deposits regulation',
]
STRONG={
  "tokenized":3,"tokenization":3,"tokenized fund":4,"tokenized treasury":4,
  "tokenized securities":4,"tokenized stocks":4,"tokenized deposits":4,
  "deposit token":4,"onchain finance":3,"real world asset":3,"rwa":2,
  "digital bond":3,"private credit":2,"stablecoin":1,
}
INSTITUTIONAL={
  "blackrock":3,"franklin templeton":3,"jpmorgan":3,"j.p. morgan":3,"dtcc":3,
  "securitize":2,"ondo":2,"centrifuge":2,"chainlink":2,"bank":1,"fund":1,
  "asset manager":2,"securities":2,"treasury":2,"institution":1,"settlement":2,
  "exchange":1,"custody":1,"regulator":1,
}
BLOCK=["price prediction","airdrop","presale","memecoin","meme coin","casino","100x","price target","giveaway"]

def clean(s):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()

def slugify(s):
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:80].rstrip("-")

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"RWA-Wire-News-Watch/1.0"})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()

def main():
    state=json.loads(STATE.read_text()) if STATE.exists() else {"seen":[]}
    seen=set(state.get("seen",[]))
    existing=" ".join(p.stem for p in INBOX.glob("*.json")) if INBOX.exists() else ""
    now=datetime.now(timezone.utc); items=[]
    for q in QUERIES:
        url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q+" when:2d","hl":"en-US","gl":"US","ceid":"US:en"})
        try: root=ET.fromstring(fetch(url))
        except Exception as e:
            print("feed error",q,e,file=sys.stderr); continue
        for x in root.findall(".//item"):
            title=clean(x.findtext("title")); link=clean(x.findtext("link")); desc=clean(x.findtext("description"))
            guid=clean(x.findtext("guid")) or link
            try: published=parsedate_to_datetime(x.findtext("pubDate")).astimezone(timezone.utc)
            except Exception: published=now
            hay=(title+" "+desc).lower()
            score=sum(weight for k,weight in STRONG.items() if k in hay)+sum(weight for k,weight in INSTITUTIONAL.items() if k in hay)-sum(8 for k in BLOCK if k in hay)
            if guid in seen or slugify(title) in existing or now-published>timedelta(hours=48): continue
            # Require an actual tokenization/RWA signal; institution names alone are not enough.
            has_rwa_signal=any(k in hay for k in STRONG if k != "stablecoin")
            if score>=6 and has_rwa_signal: items.append((score,published,title,link,desc,guid))
    if not items:
        print("No new high-confidence story found."); return
    items.sort(key=lambda x:(x[0],x[1]),reverse=True)
    score,published,title,link,desc,guid=items[0]
    # Google News descriptions are discovery metadata, not independent verification.
    # Keep automated copy conservative and source-attributed.
    source_name=title.rsplit(" - ",1)[-1] if " - " in title else "Google News source"
    clean_title=title.rsplit(" - ",1)[0] if " - " in title else title
    summary=desc or f"A new institutional tokenization development has been reported: {clean_title}."
    # RSS descriptions often repeat the headline and publisher name. Do not turn
    # that discovery noise into public-facing copy.
    if source_name and summary.endswith(source_name):
        summary=summary[:-len(source_name)].strip(" -|")
    if summary.strip().lower()==clean_title.strip().lower() or len(summary)<40:
        summary=f"{clean_title}. RWA Wire is tracking the development for its relevance to institutional tokenization."
    if len(summary)>420: summary=summary[:417].rstrip()+"..."
    why="The development connects tokenized assets with institutional financial infrastructure, showing how onchain instruments are moving into practical market workflows."
    body=(f"{summary}\n\n"
          "## Why it matters\n\n"
          f"{why}\n\n"
          "## What to watch\n\n"
          "Watch for additional details on eligibility, custody, settlement and how the tokenized asset is used in production. RWA Wire will update coverage as stronger source material becomes available.")
    day=published.date().isoformat(); slug=slugify(clean_title)
    brief={"title":clean_title,"description":summary,"why_it_matters":why,"pubDate":day,"category":"news",
      "tags":["Tokenization","Institutions","News Watch"],"keyTakeaways":[summary,why],"body":body,
      "sources":[{"name":source_name,"url":link}],"newsWatch":{"score":score,"discoveredAt":now.isoformat(),"requiresSourceReview":True}}
    INBOX.mkdir(parents=True,exist_ok=True); path=INBOX/f"{day}-{slug}.json"
    path.write_text(json.dumps(brief,indent=2,ensure_ascii=False)+"\n")
    seen.add(guid); state["seen"]=list(seen)[-500:]; state["lastRun"]=now.isoformat(); state["lastCandidate"]=str(path.relative_to(ROOT))
    STATE.write_text(json.dumps(state,indent=2)+"\n")
    print(path.relative_to(ROOT))

if __name__=="__main__": main()
