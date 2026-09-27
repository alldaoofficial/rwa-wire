#!/usr/bin/env python3
import json, os, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "publish" / "candidates"
APPROVED = ROOT / "publish" / "approved"
REJECTED = ROOT / "publish" / "rejected"

def load_candidate(path_text):
    p = (ROOT / path_text).resolve()
    if CANDIDATES.resolve() not in p.parents or p.suffix != ".json":
        raise SystemExit("Candidate path must be publish/candidates/*.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    for key in ("id","title","category","why_it_matters","article_url","image_url","caption","sources"):
        if not data.get(key):
            raise SystemExit(f"Missing candidate field: {key}")
    return p, data

def telegram(method, payload):
    token=os.environ["TELEGRAM_BOT_TOKEN"]
    req=urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(payload).encode(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result=json.loads(r.read().decode())
    if not result.get("ok"):
        raise SystemExit(f"Telegram {method} failed")
    return result["result"]

def request(path_text):
    _, c=load_candidate(path_text)
    chat=os.environ.get("TELEGRAM_REVIEW_CHAT_ID","").strip()
    if not chat:
        raise SystemExit("TELEGRAM_REVIEW_CHAT_ID secret is required.")
    sources=" · ".join(s.get("name","Source") if isinstance(s,dict) else str(s) for s in c["sources"])
    text=(
      "RWA WIRE // STORY READY\n\n"
      f"{c['title']}\n\n"
      f"{str(c['category']).upper()} //\n"
      f"{c['why_it_matters']}\n\n"
      f"Sources: {sources}\n\n"
      "Prepared:\n✓ Article\n✓ Sources\n✓ SEO\n✓ Visual\n✓ Telegram draft\n✓ Duplicate ID\n\n"
      "Open the preview, then approve or reject."
    )
    # Buttons intentionally use deep links to a tiny approval endpoint that will be
    # connected in phase 2. Until then, the review card is safe/read-only.
    keyboard={"inline_keyboard":[
      [{"text":"👁 Preview","url":c["article_url"]}],
      [{"text":"✅ APPROVE","callback_data":f"approve:{c['id']}"},
       {"text":"❌ REJECT","callback_data":f"reject:{c['id']}"}]
    ]}
    telegram("sendMessage",{"chat_id":chat,"text":text,"reply_markup":json.dumps(keyboard)})
    print("Editorial approval card sent.")

if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1]!="request":
        raise SystemExit("Usage: editorial_approval.py request publish/candidates/<id>.json")
    request(sys.argv[2])
