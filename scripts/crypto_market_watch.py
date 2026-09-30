#!/usr/bin/env python3
"""Discover high-signal crypto market developments for RWA Wire.

This is deliberately separate from the RWA News Watch. It covers only market-wide
crypto developments with institutional/macro relevance and rejects routine altcoin,
prediction, meme and promotional coverage.
"""
import html, json, pathlib, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'publish/crypto-market-watch-state.json'
INBOX=ROOT/'publish/inbox'
QUERIES=[
 'bitcoin ethereum crypto market institutional flows ETF when:1d',
 'bitcoin ethereum crypto market liquidation volatility macro when:1d',
 'bitcoin ETF ethereum ETF inflows outflows institutions when:1d',
 'crypto market Federal Reserve rates inflation dollar treasury yields when:1d',
 'crypto regulation SEC CFTC stablecoin market structure when:1d',
 'bitcoin ethereum exchange liquidity derivatives open interest when:1d',
]
PRIMARY={'sec','cftc','federal reserve','ecb','bank of england','bis','blackrock','fidelity','coinbase','cme group','nasdaq'}
TRUSTED={'reuters','bloomberg','financial times','cnbc','coindesk','the block','fortune','wsj','wall street journal','blockworks','dl news'}
BLOCK=['price prediction','price target','presale','airdrop','100x','memecoin','meme coin','best crypto','best altcoin','buy now','giveaway','moonshot','sponsored','promoted content','technical analysis','could reach','will reach']
MARKET=['bitcoin','btc','ethereum','eth','crypto market','digital asset']
SIGNAL={'etf':3,'inflow':2,'outflow':2,'liquidation':2,'volatility':1,'federal reserve':3,'interest rate':2,'inflation':2,'treasury yield':2,'sec':2,'cftc':2,'regulation':2,'market structure':3,'institutional':2,'open interest':2,'derivatives':2,'liquidity':2,'stablecoin':1,'record high':1,'record low':1}

def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:80].rstrip('-')
def norm_source(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def tier(source):
 s=norm_source(source)
 if any(k==s or k in s for k in PRIMARY): return 'primary'
 if any(k==s or k in s for k in TRUSTED): return 'trusted'
 return 'other'
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'RWA-Wire-Crypto-Market-Watch/1.0'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def tokens(s): return {x for x in re.findall(r'[a-z0-9]+',s.lower()) if len(x)>2}
def similar(a,b):
 aa,bb=tokens(a),tokens(b)
 return bool(aa and bb and len(aa&bb)>=4 and len(aa&bb)/min(len(aa),len(bb))>=.55)

def main():
 state=json.loads(STATE.read_text()) if STATE.exists() else {'seen':[]}; seen=set(state.get('seen',[])); now=datetime.now(timezone.utc)
 existing=[]
 for folder in [ROOT/'publish/inbox',ROOT/'publish/candidates',ROOT/'publish/approved',ROOT/'publish/distribution']:
  if folder.exists():
   for p in folder.glob('*.json'):
    try:
     d=json.loads(p.read_text(encoding='utf-8')); existing.append(str(d.get('title','')))
    except Exception: pass
 article_dir=ROOT/'src/content/articles'
 if article_dir.exists(): existing += [p.stem.replace('-',' ') for p in article_dir.glob('*.mdx')]
 candidates=[]; scan=[]; raw=unique=blocked=untrusted=low_signal=0
 for q in QUERIES:
  url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'en-US','gl':'US','ceid':'US:en'})
  try: root=ET.fromstring(fetch(url))
  except Exception: continue
  for item in root.findall('.//item'):
   raw+=1; title=clean(item.findtext('title')); desc=clean(item.findtext('description')); link=clean(item.findtext('link')); guid=clean(item.findtext('guid')) or link
   headline=title.rsplit(' - ',1)[0] if ' - ' in title else title; source=title.rsplit(' - ',1)[-1] if ' - ' in title else ''
   if guid in seen or any(similar(headline,x) for x in scan): continue
   scan.append(headline); unique+=1; hay=(headline+' '+desc).lower()
   if any(x in hay for x in BLOCK): blocked+=1; continue
   if not any(x in hay for x in MARKET): low_signal+=1; continue
   trust=tier(source)
   if trust not in {'primary','trusted'}: untrusted+=1; continue
   score=sum(v for k,v in SIGNAL.items() if k in hay)
   if score<4: low_signal+=1; continue
   try: published=parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc)
   except Exception: published=now
   if now-published>timedelta(hours=30): continue
   if any(similar(headline,x) for x in existing): continue
   candidates.append((score,published,headline,desc,link,guid,source,trust))
 diagnostics={'rawItems':raw,'uniqueItems':unique,'qualified':len(candidates),'blocked':blocked,'untrusted':untrusted,'lowSignal':low_signal}
 state['lastRun']=now.isoformat(); state['lastDiagnostics']=diagnostics
 if not candidates:
  state['lastResult']='no-qualified-story'; STATE.write_text(json.dumps(state,indent=2)+'\n'); print('Crypto Market Watch:',json.dumps(diagnostics)); return
 candidates.sort(key=lambda x:(x[0],x[1]),reverse=True); score,published,title,desc,link,guid,source,trust=candidates[0]
 summary=desc if len(desc)>=50 else f'{title}. RWA Wire is tracking the development for its impact on crypto market structure and institutional risk appetite.'
 summary=summary[:417].rstrip()+('...' if len(summary)>417 else '')
 why='This is a market-wide signal that can affect crypto liquidity, institutional positioning and the environment in which tokenized assets trade and grow.'
 body=f'''{summary}\n\n## Market context\n\n{why}\n\n## Why RWA Wire is watching\n\nBroader crypto liquidity and institutional risk appetite influence capital formation across tokenized finance. We track these market-wide developments without turning RWA Wire into a general altcoin news feed.\n\n## What to watch\n\nWatch follow-through in Bitcoin and Ethereum liquidity, institutional flows, derivatives positioning and any spillover into tokenized-asset markets.'''
 day=published.date().isoformat(); brief={'title':title,'description':summary,'why_it_matters':why,'pubDate':day,'category':'markets','reviewCategory':'CRYPTO MARKET','tags':['Crypto Market','Bitcoin','Ethereum','Institutions'],'keyTakeaways':[summary,why],'body':body,'sources':[{'name':source,'url':link}], 'cryptoWatch':{'score':score,'sourceTrust':trust,'discoveredAt':now.isoformat(),'autoPublishEligible':True}}
 INBOX.mkdir(parents=True,exist_ok=True); path=INBOX/f'{day}-{slug(title)}.json'; path.write_text(json.dumps(brief,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 seen.add(guid); state['seen']=list(seen)[-500:]; state['lastResult']='candidate'; state['lastCandidate']=str(path.relative_to(ROOT)); STATE.write_text(json.dumps(state,indent=2)+'\n'); print('Crypto Market Watch:',json.dumps(diagnostics)); print(path.relative_to(ROOT))
if __name__=='__main__': main()
