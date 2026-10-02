#!/usr/bin/env python3
"""Create reusable distribution assets from an approved RWA Wire manifest."""
import json, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit("Usage: distribution_package.py publish/approved/<id>.json")
p=(ROOT/sys.argv[1]).resolve(); approved=(ROOT/"publish/approved").resolve()
if approved not in p.parents or p.suffix!=".json": raise SystemExit("Invalid approved manifest path")
d=json.loads(p.read_text(encoding="utf-8")); dist=d.get("distribution") or {}
caption=str(d.get("caption","")).strip(); article=str(d.get("article_url","")).strip(); image=str(d.get("image_url","")).strip()
title=str(d.get("title","")).strip(); why=str(d.get("why_it_matters","")).strip(); category=str(d.get("category","NEWS")).strip().upper() or "NEWS"
priority=str(d.get("priority",d.get("severity",d.get("classification","")))).strip().lower()
def clean(s): return re.sub(r"\s+"," ",str(s or "")).strip()
def useful(s):
 s=clean(s); generic=("the development connects","rwa wire is tracking","this development highlights","the move underscores")
 return s if s and not any(g in s.lower() for g in generic) else ""
def x_copy():
 label="BREAKING" if priority=="breaking" else "DEVELOPING" if priority in {"important","developing"} else category
 headline=clean(title)
 detail=useful(dist.get("summary")) or useful(why)
 # Social is the hook, not the article. Keep context deliberately concise so the
 # destination contains materially more value than the X/Telegram post.
 parts=[f"{label}: {headline}"]
 if detail and clean(detail).lower()!=clean(headline).lower(): parts += ["", detail[:150].rstrip()+("…" if len(detail)>150 else "")]
 parts += ["", "Full analysis ↓", article]
 return "\n".join(parts).strip()
out={"id":d.get("id",p.stem),"article_url":article,"image_url":image,"telegram":dist.get("telegram") or caption,"x":x_copy(),"breaking":dist.get("breaking") or f"RWA WIRE // {category}\n\n{title}\n\n{article}","summary":dist.get("summary") or why,"status":"approved_distribution_package"}
target=ROOT/"publish/distribution"/f"{out['id']}.json"; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(target.relative_to(ROOT))
