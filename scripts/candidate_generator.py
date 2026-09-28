#!/usr/bin/env python3
"""Build a validated RWA Wire story package from a reviewed JSON brief.

This generator is intentionally deterministic: source research/editorial facts enter
through the brief, while the script enforces schema, URLs, disclosure and visual
format before creating article + visual + candidate.
"""
import argparse, html, json, pathlib, re
from datetime import date
from urllib.parse import urlparse

ROOT=pathlib.Path(__file__).resolve().parents[1]
ARTICLES=ROOT/"src/content/articles"
IMAGES=ROOT/"public/images/news"
CANDIDATES=ROOT/"publish/candidates"
ALLOWED={"news","rwa","tokenization","institutions","markets","projects","learn"}

def slugify(s):
    s=re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
    if not s: raise ValueError("Empty slug")
    return s

def esc_yaml(s): return json.dumps(str(s), ensure_ascii=False)
def mdlink(x): return f'[{x["name"]}]({x["url"]})'

def validate(d):
    for k in ("title","description","why_it_matters","body","sources"):
        if not d.get(k): raise ValueError(f"Missing {k}")
    if not isinstance(d["sources"],list) or not d["sources"]: raise ValueError("sources must be non-empty")
    for s in d["sources"]:
        if not s.get("name") or not s.get("url") or urlparse(s["url"]).scheme!="https":
            raise ValueError("Every source needs name + HTTPS url")
    cat=d.get("category","news")
    if cat not in ALLOWED: raise ValueError(f"Invalid category: {cat}")
    if len(d.get("caption",""))>1024: raise ValueError("caption exceeds Telegram limit")

def svg(title, category):
    t=html.escape(title); c=html.escape(category.upper())
    words=t.split()
    lines=[]; line=""
    for word in words:
        test=(line+" "+word).strip()
        if len(test)>30 and line:
            lines.append(line); line=word
        else:
            line=test
    if line: lines.append(line)
    lines=lines[:4]
    tspans="".join(f'<tspan x="86" dy="{0 if i==0 else 68}">{x}</tspan>' for i,x in enumerate(lines))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0D1217"/><stop offset="1" stop-color="#080A0D"/></linearGradient>
  <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#1A2229" stroke-width="1"/></pattern>
</defs>
<rect width="1200" height="675" fill="url(#g)"/><rect width="1200" height="675" fill="url(#grid)" opacity=".7"/>
<rect x="0" width="10" height="675" fill="#2ED47A"/>
<text x="86" y="82" fill="#2ED47A" font-family="Arial,sans-serif" font-size="18" font-weight="700" letter-spacing="4">RWA WIRE // {c}</text>
<text x="1114" y="82" text-anchor="end" fill="#66717B" font-family="Arial,sans-serif" font-size="14" letter-spacing="3">INTELLIGENCE BRIEF</text>
<path d="M86 112H1114" stroke="#263038"/>
<text x="86" y="206" fill="#F5F7FA" font-family="Georgia,serif" font-size="58" font-weight="600">{tspans}</text>
<g transform="translate(905 440)" opacity=".9"><circle cx="100" cy="70" r="96" fill="none" stroke="#263038"/><circle cx="100" cy="70" r="58" fill="none" stroke="#2ED47A"/><path d="M4 70h192M100-26v192" stroke="#263038"/><circle cx="100" cy="70" r="7" fill="#2ED47A"/></g>
<path d="M86 566H1114" stroke="#263038"/>
<text x="86" y="610" fill="#8B949E" font-family="Arial,sans-serif" font-size="15" letter-spacing="2">REAL-WORLD ASSETS · TOKENIZATION · INSTITUTIONS · MARKETS</text>
<text x="1114" y="610" text-anchor="end" fill="#2ED47A" font-family="Arial,sans-serif" font-size="15" font-weight="700">THERWAWIRE.COM</text>
</svg>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("brief"); a=ap.parse_args()
    d=json.loads(pathlib.Path(a.brief).read_text(encoding="utf-8")); validate(d)
    slug=slugify(d.get("slug") or d["title"]); pub=d.get("pubDate") or date.today().isoformat()
    article_url=f"https://therwawire.com/news/{slug}/"; image_url=f"https://therwawire.com/images/news/{slug}.svg"
    tags=d.get("tags") or ["News","RWA","Tokenization"]
    take=d.get("keyTakeaways") or [d["why_it_matters"]]
    body=d["body"].strip()
    sources="\n".join(f"- {mdlink(s)}" for s in d["sources"])
    fm=[
      "---",'type: "NEWS"',f'category: {esc_yaml(d.get("category","news"))}',f'title: {esc_yaml(d["title"])}',
      f'description: {esc_yaml(d["description"])}',f'pubDate: {esc_yaml(pub)}',
      f'readingTime: {esc_yaml(d.get("readingTime","4 min read"))}',f'heroImage: {esc_yaml("/images/news/"+slug+".svg")}',
      f'heroImageAlt: {esc_yaml(d.get("heroImageAlt", "RWA Wire editorial visual for "+d["title"]))}',
      "tags: "+json.dumps(tags,ensure_ascii=False),'relatedSlugs: []',"showTradingCTA: false","keyTakeaways:"
    ]+[f"  - {esc_yaml(x)}" for x in take]+["---"]
    article="\n".join(fm)+"\n\n"+body+"\n\n---\n\n**Primary sources**\n\n"+sources+"\n\n*RWA Wire covers real-world assets, tokenization and the infrastructure transforming global finance.*\n"
    caption=d.get("caption") or f'{d["title"]}\n\n{d["why_it_matters"]}\n\nRead the full story →\n{article_url}\n\nTrading partner: Bitunix · Affiliate link · Trading involves risk.'
    if len(caption)>1024: raise ValueError("generated caption exceeds Telegram limit")
    candidate_id=f"{pub}-{slug}"[:55].rstrip("-")
    social=d.get("social") or {}
    distribution={
      "telegram": caption,
      "x": social.get("x") or f'{d["title"]}\n\n{d["why_it_matters"]}\n\n{article_url}',
      "breaking": social.get("breaking") or f'RWA WIRE // {d.get("reviewCategory",d.get("category","news")).upper()}\n\n{d["title"]}\n\n{article_url}',
      "summary": social.get("summary") or d["description"],
    }
    candidate={"id":candidate_id,"title":d["title"],"category":d.get("reviewCategory",d.get("category","news")).upper(),
      "why_it_matters":d["why_it_matters"],"article_url":article_url,"image_url":image_url,"caption":caption,
      "distribution":distribution,"sources":d["sources"]}
    for p in (ARTICLES/f"{slug}.mdx",IMAGES/f"{slug}.svg",CANDIDATES/f'{candidate["id"]}.json'):
        if p.exists(): raise ValueError(f"Refusing overwrite: {p.relative_to(ROOT)}")
    ARTICLES.mkdir(parents=True,exist_ok=True); IMAGES.mkdir(parents=True,exist_ok=True); CANDIDATES.mkdir(parents=True,exist_ok=True)
    (ARTICLES/f"{slug}.mdx").write_text(article,encoding="utf-8")
    (IMAGES/f"{slug}.svg").write_text(svg(d["title"],d.get("reviewCategory","NEWS")),encoding="utf-8")
    cp=CANDIDATES/f'{candidate["id"]}.json'; cp.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(cp.relative_to(ROOT))

if __name__=="__main__": main()
