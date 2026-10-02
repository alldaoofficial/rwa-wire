#!/usr/bin/env python3
"""Publish an approved RWA Wire distribution package or Market Pulse to X."""
import base64, hashlib, hmac, json, os, pathlib, secrets, sys, time, urllib.parse, urllib.request, urllib.error, uuid
from io import BytesIO
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit("Usage: x_publish.py <distribution-or-market-pulse.json>")
p=(ROOT/sys.argv[1]).resolve(); dist_root=(ROOT/"publish/distribution").resolve(); pulse_root=(ROOT/"publish/market-pulse").resolve()
if p.suffix!=".json" or not (dist_root in p.parents or pulse_root in p.parents): raise SystemExit("Invalid X package path")
d=json.loads(p.read_text(encoding="utf-8")); publish_id=str(d.get("id",p.stem)).strip(); is_pulse=pulse_root in p.parents
text=str(d.get("x","")).strip(); article=str(d.get("article_url","")).strip(); image_url=str(d.get("image_url","")).strip()
if not text: raise SystemExit("Package has no X copy")
if article and article not in text: text=f"{text}\n\nFull analysis ↓\n{article}"
TCO_URL_LENGTH=23
def weighted_length(s): return len(s)-len(article)+TCO_URL_LENGTH if article and article in s else len(s)
if weighted_length(text)>280:
 suffix=f"\n\nFull analysis ↓\n{article}" if article else ""; body=text.replace(article,"").replace("Full analysis ↓","").replace("Full story ↓","").strip(); budget=280-weighted_length(suffix)-1
 body=body[:max(40,budget)].rstrip(" .,-:;"); body += "…" if len(body)<len(text.replace(article,"").strip()) else ""; text=f"{body}{suffix}" if suffix else body
if weighted_length(text)>280: raise SystemExit("Generated X copy exceeds 280 weighted characters")
marker_dir=ROOT/("publish/market-pulse-x-posted" if is_pulse else "publish/x-posted"); marker=marker_dir/f"{publish_id}.json"
if marker.exists(): raise SystemExit("This publish id has already been posted to X")
ck=os.environ["X_API_KEY"]; cs=os.environ["X_API_SECRET"]; at=os.environ["X_ACCESS_TOKEN"]; ats=os.environ["X_ACCESS_TOKEN_SECRET"]
enc=lambda s: urllib.parse.quote(str(s),safe="~-._")
def auth_header(method,url,extra=None):
 oauth={"oauth_consumer_key":ck,"oauth_nonce":secrets.token_hex(16),"oauth_signature_method":"HMAC-SHA1","oauth_timestamp":str(int(time.time())),"oauth_token":at,"oauth_version":"1.0"}
 params={**oauth,**(extra or {})}; param="&".join(f"{enc(k)}={enc(v)}" for k,v in sorted(params.items())); base="&".join([method,enc(url),enc(param)]); key=f"{enc(cs)}&{enc(ats)}"
 oauth["oauth_signature"]=base64.b64encode(hmac.new(key.encode(),base.encode(),hashlib.sha1).digest()).decode()
 return "OAuth "+", ".join(f'{enc(k)}="{enc(v)}"' for k,v in sorted(oauth.items()))
def load_news_image(url):
 if not url:return None
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RWA-Wire-X-Publisher/1.3'}),timeout=30) as r: raw=r.read()
 if url.lower().split('?')[0].endswith('.svg') or raw.lstrip().startswith(b'<svg'):
  import cairosvg; raw=cairosvg.svg2png(bytestring=raw,output_width=1200,output_height=675)
 from PIL import Image
 im=Image.open(BytesIO(raw)).convert('RGB'); out=BytesIO(); im.save(out,'JPEG',quality=92,optimize=True); return out.getvalue()
def upload_media(raw):
 url='https://upload.twitter.com/1.1/media/upload.json'; boundary='----RWAWire'+uuid.uuid4().hex; body=bytearray()
 body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="rwa-wire.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()); body.extend(raw); body.extend(f'\r\n--{boundary}--\r\n'.encode())
 req=urllib.request.Request(url,data=bytes(body),method='POST',headers={'Authorization':auth_header('POST',url),'Content-Type':f'multipart/form-data; boundary={boundary}','User-Agent':'RWA-Wire-X-Publisher/1.3'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r: result=json.loads(r.read().decode())
 except urllib.error.HTTPError as e: raise SystemExit(f"X media upload HTTP {e.code}: {e.read().decode(errors='replace')[:1000]}")
 mid=str(result.get('media_id_string') or result.get('media_id') or '').strip()
 if not mid: raise SystemExit(f'X media upload did not return media id: {result}')
 return mid
media_id=None
if not is_pulse and image_url: media_id=upload_media(load_news_image(image_url))
url="https://api.x.com/2/tweets"; payload={"text":text}
if media_id: payload['media']={'media_ids':[media_id]}
req=urllib.request.Request(url,data=json.dumps(payload).encode(),method='POST',headers={"Authorization":auth_header('POST',url),"Content-Type":"application/json","User-Agent":"RWA-Wire-X-Publisher/1.3"})
try:
 with urllib.request.urlopen(req,timeout=30) as r: result=json.loads(r.read().decode())
except urllib.error.HTTPError as e: raise SystemExit(f"X API HTTP {e.code}: {e.read().decode(errors='replace')[:1000]}")
tweet_id=str((result.get("data") or {}).get("id","")).strip()
if not tweet_id: raise SystemExit(f"X API did not confirm publication: {result}")
marker_dir.mkdir(parents=True,exist_ok=True); marker.write_text(json.dumps({"id":publish_id,"status":"published","tweet_id":tweet_id,"article_url":article,"media_attached":bool(media_id),"type":"market_pulse" if is_pulse else "news"},indent=2)+"\n"); print(f"Published RWA Wire {'Market Pulse' if is_pulse else 'post'} to X: {tweet_id} (media={bool(media_id)})")
