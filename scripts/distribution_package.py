#!/usr/bin/env python3
"""Create reusable distribution assets from an approved RWA Wire manifest."""
import json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit("Usage: distribution_package.py publish/approved/<id>.json")
p=(ROOT/sys.argv[1]).resolve()
approved=(ROOT/"publish/approved").resolve()
if approved not in p.parents or p.suffix!=".json": raise SystemExit("Invalid approved manifest path")
d=json.loads(p.read_text(encoding="utf-8"))
dist=d.get("distribution") or {}
caption=str(d.get("caption","")).strip()
article=str(d.get("article_url","")).strip()
title=str(d.get("title","")).strip()
why=str(d.get("why_it_matters","")).strip()
out={
 "id":d.get("id",p.stem),"article_url":article,
 "telegram":dist.get("telegram") or caption,
 "x":dist.get("x") or f"{title}\n\n{why}\n\n{article}",
 "breaking":dist.get("breaking") or f"RWA WIRE // {d.get('category','NEWS')}\n\n{title}\n\n{article}",
 "summary":dist.get("summary") or why,
 "status":"approved_distribution_package"
}
target=ROOT/"publish/distribution"/f"{out['id']}.json";target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(target.relative_to(ROOT))
