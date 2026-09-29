#!/usr/bin/env python3
"""Publish an approved RWA Wire distribution package to X using OAuth 1.0a."""
import base64, hashlib, hmac, json, os, pathlib, secrets, sys, time, urllib.parse, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit("Usage: x_publish.py publish/distribution/<id>.json")
p=(ROOT/sys.argv[1]).resolve(); dist_root=(ROOT/"publish/distribution").resolve()
if dist_root not in p.parents or p.suffix!=".json": raise SystemExit("Invalid distribution package path")
d=json.loads(p.read_text(encoding="utf-8")); publish_id=str(d.get("id",p.stem)).strip()
text=str(d.get("x","")).strip(); article=str(d.get("article_url","")).strip()
if not text: raise SystemExit("Distribution package has no X copy")
if article and article not in text: text=f"{text}\n\n{article}"
# X shortens URLs server-side, but keep editorial copy compact before submission.
if len(text)>280:
    reserve=len(article)+2 if article else 0
    body=text.replace(article,"").strip() if article else text
    body=body[:max(40,277-reserve)].rstrip(" .,-")+"…"
    text=f"{body}\n\n{article}" if article else body
marker=ROOT/"publish/x-posted"/f"{publish_id}.json"
if marker.exists(): raise SystemExit("This publish id has already been posted to X")
ck=os.environ["X_API_KEY"]; cs=os.environ["X_API_SECRET"]; at=os.environ["X_ACCESS_TOKEN"]; ats=os.environ["X_ACCESS_TOKEN_SECRET"]
url="https://api.x.com/2/tweets"; method="POST"
oauth={"oauth_consumer_key":ck,"oauth_nonce":secrets.token_hex(16),"oauth_signature_method":"HMAC-SHA1","oauth_timestamp":str(int(time.time())),"oauth_token":at,"oauth_version":"1.0"}
enc=lambda s: urllib.parse.quote(str(s),safe="~-._")
param="&".join(f"{enc(k)}={enc(v)}" for k,v in sorted(oauth.items()))
base="&".join([method,enc(url),enc(param)]); key=f"{enc(cs)}&{enc(ats)}"
oauth["oauth_signature"]=base64.b64encode(hmac.new(key.encode(),base.encode(),hashlib.sha1).digest()).decode()
auth="OAuth "+", ".join(f'{enc(k)}="{enc(v)}"' for k,v in sorted(oauth.items()))
req=urllib.request.Request(url,data=json.dumps({"text":text}).encode(),method=method,headers={"Authorization":auth,"Content-Type":"application/json","User-Agent":"RWA-Wire-X-Publisher/1.0"})
try:
    with urllib.request.urlopen(req,timeout=30) as r: result=json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    raise SystemExit(f"X API HTTP {e.code}: {e.read().decode(errors='replace')[:1000]}")
tweet_id=str((result.get("data") or {}).get("id","")).strip()
if not tweet_id: raise SystemExit(f"X API did not confirm publication: {result}")
marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text(json.dumps({"id":publish_id,"status":"published","tweet_id":tweet_id,"article_url":article},indent=2)+"\n")
print(f"Published RWA Wire post to X: {tweet_id}")
