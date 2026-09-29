#!/usr/bin/env python3
"""Scheduled discovery for RWA Wire with transparent qualification diagnostics."""
import html, json, pathlib, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
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
  'tokenization pilot bank asset manager exchange settlement custody',
  'digital asset securities tokenization regulator infrastructure',
]
STRONG={"tokenized":3,"tokenization":3,"tokenized fund":4,"tokenized treasury":4,"tokenized securities":4,"tokenized stocks":4,"tokenized deposits":4,"deposit token":4,"onchain finance":3,"real world asset":3,"rwa":2,"digital bond":3,"private credit":2,"stablecoin":1,"digital securities":3,"tokenization pilot":3}
INSTITUTIONAL={"blackrock":3,"franklin templeton":3,"jpmorgan":3,"j.p. morgan":3,"dtcc":3,"securitize":2,"ondo":2,"centrifuge":2,"chainlink":2,"bank":1,"fund":1,"asset manager":2,"securities":2,"treasury":2,"institution":1,"settlement":2,"exchange":1,"custody":1,"regulator":1,"clearstream":2,"euroclear":2,"swift":2,"mastercard":2,"visa":2,"state street":2,"fidelity":2,"wisdomtree":2}
BLOCK=["price prediction","airdrop","presale","memecoin","meme coin","casino","100x","price target","giveaway","best crypto","best altcoin","to invest in","top crypto","next crypto","buy now","massive gains","explosive growth","hidden gem","moonshot","can x reach","price forecast","price outlook","sponsored","partner content","promoted content"]
HARD_BLOCK=["best crypto","to invest in","presale","100x","price prediction","price target","giveaway","moonshot","sponsored","promoted content"]
PRIMARY_SOURCES={"blackrock","franklin templeton","jpmorgan","j p morgan","dtcc","securitize","ondo finance","centrifuge","chainlink","sec gov","u s securities and exchange commission","federal reserve","ecb","european central bank","bis","bank for international settlements","swift","euroclear","clearstream","state street","fidelity","wisdomtree","mastercard","visa","bank of england","monetary authority of singapore","mas","hong kong monetary authority","hkma"}
TRUSTED_MEDIA={"reuters","bloomberg","financial times","the wall street journal","wsj","coindesk","the block","fortune","forbes","cnbc","decrypt","dl news","blockworks","ledger insights","ledgerinsights","american banker"}
SPECIALIST_MEDIA={"securities io","securities","financefeeds","fintech futures","the digital banker","globalcustodian","funds europe","finextra","banking dive","pymnts"}
WIRE_SERVICES={"business wire","businesswire","pr newswire","prnewswire","globe newswire","globenewswire","accesswire"}
LOW_TRUST_HINTS={"coinmarketcap","investing com","investing","tradingview","benzinga","cryptopolitan","coinpedia","u today","the crypto basic","crypto news flash","blockchain reporter"}
STOPWORDS={"the","a","an","and","or","of","to","in","on","for","as","with","its","is","are","adds","turns","brings","into","from","at","by"}

def normalize_source(name):
    s=(name or "").strip().lower()
    s=re.sub(r"^https?://(?:www\.)?","",s)
    s=s.split("/",1)[0]
    s=re.sub(r"\.(?:com|org|net|io|co|news|finance|media|ai|us|uk|au)(?:\.[a-z]{2})?$","",s)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def source_tier(name):
    raw=(name or "").strip().lower(); s=normalize_source(raw)
    variants={raw,s,s.replace(" ","")}
    def hit(keys):
        return any(any(k in v or v in k for v in variants if v) for k in keys)
    if hit(PRIMARY_SOURCES): return "primary"
    if hit(TRUSTED_MEDIA): return "trusted"
    if hit(SPECIALIST_MEDIA): return "specialist"
    if hit(WIRE_SERVICES): return "wire"
    if hit(LOW_TRUST_HINTS): return "low"
    return "unknown"

def clean(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
def slugify(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:80].rstrip("-")
def story_tokens(s): return {w for w in re.findall(r"[a-z0-9]+",s.lower()) if len(w)>2 and w not in STOPWORDS}
def same_story(a,b):
    aa,bb=story_tokens(a),story_tokens(b)
    if not aa or not bb:return False
    overlap=len(aa & bb)
    return overlap>=4 and overlap/min(len(aa),len(bb))>=0.55

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"RWA-Wire-News-Watch/1.3"})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()

def classify(score,trust,has_rwa_signal):
    if has_rwa_signal and trust in {"primary","trusted"} and score>=9:return "breaking"
    if has_rwa_signal and trust in {"primary","trusted"} and score>=6:return "important"
    if has_rwa_signal and score>=4:return "watchlist"
    return "reject"

def main():
    state=json.loads(STATE.read_text()) if STATE.exists() else {"seen":[]}; seen=set(state.get("seen",[]))
    pipeline_dirs=[ROOT/"publish/inbox",ROOT/"publish/candidates",ROOT/"publish/approved",ROOT/"publish/posted"]
    existing_slugs=set()
    for folder in pipeline_dirs:
        if folder.exists(): existing_slugs.update(p.stem[11:] if re.match(r"^\d{4}-\d{2}-\d{2}-",p.stem) else p.stem for p in folder.glob("*.json"))
    article_dir=ROOT/"src/content/articles"
    if article_dir.exists(): existing_slugs.update(p.stem for p in article_dir.glob("*.mdx"))
    existing_titles=[s.replace("-"," ") for s in existing_slugs]
    for folder in pipeline_dirs:
        if folder.exists():
            for p in folder.glob("*.json"):
                try:
                    t=json.loads(p.read_text(encoding="utf-8")).get("title")
                    if t:existing_titles.append(t)
                except Exception:pass
    now=datetime.now(timezone.utc); qualified=[]; watchlist=[]; scan_titles=[]; scan_guids=set(); metrics=Counter(); rejection=Counter(); source_counts=Counter(); feed_errors=[]
    for q in QUERIES:
        url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q+" when:2d","hl":"en-US","gl":"US","ceid":"US:en"})
        try: root=ET.fromstring(fetch(url)); metrics["queries_ok"]+=1
        except Exception as e: metrics["queries_failed"]+=1; feed_errors.append(str(e)[:160]); continue
        for x in root.findall(".//item"):
            metrics["raw_items"]+=1; title=clean(x.findtext("title")); link=clean(x.findtext("link")); desc=clean(x.findtext("description")); guid=clean(x.findtext("guid")) or link
            source_name=title.rsplit(" - ",1)[-1] if " - " in title else ""; trust=source_tier(source_name); source_counts[trust]+=1
            try:published=parsedate_to_datetime(x.findtext("pubDate")).astimezone(timezone.utc)
            except Exception:published=now
            hay=(title+" "+desc).lower(); normalized_title=title.rsplit(" - ",1)[0] if " - " in title else title; headline=normalized_title.lower()
            if guid in scan_guids or any(same_story(normalized_title,t) for t in scan_titles): rejection["duplicate_in_scan"]+=1; continue
            scan_guids.add(guid); scan_titles.append(normalized_title); metrics["unique_items"]+=1
            if any(k in headline for k in HARD_BLOCK): rejection["hard_block"]+=1; continue
            score=sum(w for k,w in STRONG.items() if k in hay)+sum(w for k,w in INSTITUTIONAL.items() if k in hay)-sum(10 for k in BLOCK if k in hay)
            if guid in seen: rejection["seen_guid"]+=1; continue
            if slugify(normalized_title) in existing_slugs: rejection["existing_slug"]+=1; continue
            if any(same_story(normalized_title,t) for t in existing_titles): rejection["duplicate_story"]+=1; continue
            if now-published>timedelta(hours=48): rejection["too_old"]+=1; continue
            has_rwa_signal=any(k in hay for k in STRONG if k!="stablecoin")
            band=classify(score,trust,has_rwa_signal); record=(score,published,title,link,desc,guid,trust,source_name,band)
            if band in {"breaking","important"}: qualified.append(record); metrics[band]+=1
            elif band=="watchlist": watchlist.append(record); metrics["watchlist"]+=1; rejection[f"watchlist_{trust}"]+=1
            else:
                if not has_rwa_signal: rejection["no_rwa_signal"]+=1
                elif score<4: rejection["score_below_4"]+=1
                else: rejection["below_publish_threshold"]+=1
    top_watch=sorted(watchlist,key=lambda x:(x[0],x[1]),reverse=True)[:8]
    diagnostics={"rawItems":metrics["raw_items"],"uniqueItems":metrics["unique_items"],"queriesOk":metrics["queries_ok"],"queriesFailed":metrics["queries_failed"],"breaking":metrics["breaking"],"important":metrics["important"],"watchlist":metrics["watchlist"],"sourceTiers":dict(source_counts),"rejections":dict(rejection),"feedErrors":feed_errors[:3],"topWatchlist":[{"title":r[2].rsplit(" - ",1)[0],"source":r[7],"normalizedSource":normalize_source(r[7]),"score":r[0],"trust":r[6]} for r in top_watch]}
    state["lastRun"]=now.isoformat(); state["lastDiagnostics"]=diagnostics; print("News Watch diagnostics:",json.dumps(diagnostics,ensure_ascii=False))
    if not qualified:
        state["lastResult"]="no-qualified-story"; STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n"); print("No new high-confidence story found."); return
    qualified.sort(key=lambda x:(x[0],x[1]),reverse=True); score,published,title,link,desc,guid,trust,source_name,band=qualified[0]
    source_name=source_name or "Google News source"; clean_title=title.rsplit(" - ",1)[0] if " - " in title else title
    summary=desc or f"A new institutional tokenization development has been reported: {clean_title}."
    if source_name and summary.endswith(source_name): summary=summary[:-len(source_name)].strip(" -|")
    if summary.strip().lower()==clean_title.strip().lower() or len(summary)<40: summary=f"{clean_title}. RWA Wire is tracking the development for its relevance to institutional tokenization."
    if len(summary)>420:summary=summary[:417].rstrip()+"..."
    why="The development connects tokenized assets with institutional financial infrastructure, showing how onchain instruments are moving into practical market workflows."
    body=f"{summary}\n\n## Why it matters\n\n{why}\n\n## What to watch\n\nWatch for additional details on eligibility, custody, settlement and how the tokenized asset is used in production. RWA Wire will update coverage as stronger source material becomes available."
    day=published.date().isoformat(); slug=slugify(clean_title)
    brief={"title":clean_title,"description":summary,"why_it_matters":why,"pubDate":day,"category":"news","tags":["Tokenization","Institutions","News Watch"],"keyTakeaways":[summary,why],"body":body,"sources":[{"name":source_name,"url":link}],"newsWatch":{"score":score,"priority":band,"sourceTrust":trust,"discoveredAt":now.isoformat(),"requiresSourceReview":True,"autoPublishEligible":trust in {"primary","trusted"}}}
    INBOX.mkdir(parents=True,exist_ok=True); path=INBOX/f"{day}-{slug}.json"; path.write_text(json.dumps(brief,indent=2,ensure_ascii=False)+"\n")
    seen.add(guid); state["seen"]=list(seen)[-500:]; state["lastResult"]="candidate"; state["lastCandidate"]=str(path.relative_to(ROOT)); state["lastCandidatePriority"]=band
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n"); print(path.relative_to(ROOT))
if __name__=="__main__":main()
