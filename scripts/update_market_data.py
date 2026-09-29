#!/usr/bin/env python3
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ASSETS = {
    "chainlink": ("LINK", "Chainlink"),
    "ondo-finance": ("ONDO", "Ondo"),
    "maple-finance": ("SYRUP", "Maple Finance"),
    "zebec-protocol": ("ZBCN", "Zebec Network"),
    "plume": ("PLUME", "Plume"),
    "centrifuge": ("CFG", "Centrifuge"),
    "polymesh": ("POLYX", "Polymesh"),
    "goldfinch": ("GFI", "Goldfinch"),
    "clearpool": ("CPOOL", "Clearpool"),
    "mantra-dao": ("OM", "MANTRA"),
}
OUT = Path("public/data/markets.json")
HEADERS = {"Accept": "application/json", "User-Agent": "RWA-Wire/1.0"}

def get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def coingecko():
    ids = list(ASSETS)
    url = "https://api.coingecko.com/api/v3/simple/price?ids=" + ",".join(ids) + "&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"
    headers = dict(HEADERS)
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key
    data = get_json(url, headers)
    return {k:v for k,v in data.items() if k in ASSETS and isinstance(v,dict) and "usd" in v}

def coinpaprika():
    tickers = get_json("https://api.coinpaprika.com/v1/tickers?quotes=USD")
    result = {}
    for key, (symbol, name) in ASSETS.items():
        candidates = [t for t in tickers if str(t.get("symbol","")).upper() == symbol.upper()]
        if not candidates:
            continue
        exact = [t for t in candidates if str(t.get("name","")).lower() == name.lower()]
        t = (exact or candidates)[0]
        q = (t.get("quotes") or {}).get("USD") or {}
        if not isinstance(q.get("price"), (int,float)):
            continue
        updated = t.get("last_updated")
        ts = 0
        if updated:
            try: ts = int(datetime.fromisoformat(updated.replace("Z","+00:00")).timestamp())
            except ValueError: pass
        result[key] = {
            "usd": q.get("price"),
            "usd_market_cap": q.get("market_cap"),
            "usd_24h_vol": q.get("volume_24h"),
            "usd_24h_change": q.get("percent_change_24h"),
            "last_updated_at": ts,
        }
    return result

source = "CoinGecko"
try:
    available = coingecko()
except Exception as exc:
    print(f"CoinGecko unavailable: {exc}; trying CoinPaprika")
    available = {}

if len(available) < 4:
    source = "CoinPaprika"
    try:
        available = coinpaprika()
    except Exception as exc:
        raise SystemExit(f"All market providers unavailable: {exc}")

if len(available) < 4:
    raise SystemExit(f"Only {len(available)} tracked assets returned; refusing to replace healthy cache")

payload = {"source": source, "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"), "assets": available}
OUT.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUT.parent, delete=False) as tmp:
    json.dump(payload, tmp, separators=(",", ":"))
    tmp.write("\n")
    temp_name = tmp.name
Path(temp_name).replace(OUT)
print(f"Cached market data for {len(available)} assets from {source} at {OUT}")
