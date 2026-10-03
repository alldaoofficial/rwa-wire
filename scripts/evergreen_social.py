#!/usr/bin/env python3
"""Create one daily social package from a high-value evergreen RWA Wire guide."""
import json, pathlib, re, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
ART=ROOT/'src/content/articles'; OUT=ROOT/'publish/evergreen-social'; POSTED=ROOT/'publish/evergreen-social-posted'
BASE='https://therwawire.com'

def fm(path):
 s=path.read_text(encoding='utf-8'); m=re.match(r'^---\n(.*?)\n---\n(.*)$',s,re.S)
 if not m:return None
 head,body=m.groups(); d={}
 for line in head.splitlines():
  if ':' not in line:continue
  k,v=line.split(':',1); v=v.strip().strip('"')
  if k in {'title','description','type','category','readingTime','heroImage'}:d[k]=v
 take=re.search(r'keyTakeaways:\n((?:\s+- .*\n?)+)',head)
 d['takeaways']=[x.strip().lstrip('- ').strip('"') for x in take.group(1).splitlines()] if take else []
 d['body']=body; return d

def clean(s): return re.sub(r'\s+',' ',re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)).strip()
def shorten(s,n):
 s=clean(s)
 return s if len(s)<=n else s[:n-1].rsplit(' ',1)[0]+'…'

used={p.stem for p in POSTED.glob('*.json')} if POSTED.exists() else set(); candidates=[]
for p in ART.glob('*.mdx'):
 d=fm(p)
 if not d or d.get('type') not in {'EXPLAINER','RESEARCH'} or p.stem in used:continue
 score=0; title=d.get('title','').lower(); cat=d.get('category','')
 if cat in {'rwa','tokenization','learn','markets'}:score+=3
 if any(x in title for x in ['real-world','tokenized','tokenization','futures','leverage','copy trading','settlement']):score+=3
 score+=min(len(d['takeaways']),4); candidates.append((score,p,d))
if not candidates: raise SystemExit('No unused evergreen article available; nothing to publish')
candidates.sort(key=lambda x:(-x[0],x[1].name)); _,p,d=candidates[0]
slug=p.stem; url=f"{BASE}/{d['category']}/{slug}/"; takes=d['takeaways'][:3]
hook=shorten(d['title'].replace(' Explained','')+': what actually matters.',90); insight=shorten(takes[0] if takes else d.get('description',''),120)
x=f"{hook}\n\n{insight}\n\nRead the guide ↓\n{url}"
tg=f"📚 {d['title']}\n\n"+'\n\n'.join(f"• {shorten(t,260)}" for t in takes)+f"\n\nFull guide ({d.get('readingTime','guide')}):\n{url}"
card_url=f'{BASE}/generated/social/{slug}.jpg'
pkg={'id':slug,'kind':'evergreen','category':d.get('category','learn'),'article_url':url,'image_url':card_url,'title':d['title'],'x':x,'telegram':tg,'source_path':str(p.relative_to(ROOT)),'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
OUT.mkdir(parents=True,exist_ok=True); dest=OUT/f'{slug}.json'; dest.write_text(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(dest.relative_to(ROOT))
