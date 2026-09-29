#!/usr/bin/env python3
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ASSETS = [
    "chainlink", "ondo-finance", "maple-finance", "zebec-protocol", "plume",
    "centrifuge", "polymesh", "goldfinch", "clearpool", "mantra-dao",
]
OUT = Path("public/data/markets.json")
URL = (
    "https://api.coingecko.com/api/v3/simple/price?ids=" + ",".join(ASSETS) +
    "&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true"
    "&include_24hr_change=true&include_last_updated_at=true"
)

headers = {
    "Accept": "application/json",
    "User-Agent": "RWA-Wire/1.0 (+https://alldaoofficial.github.io/rwa-wire/)"
}
api_key = os.environ.get("COINGECKO_API_KEY", "").strip()
if api_key:
    headers["x-cg-demo-api-key"] = api_key

req = urllib.request.Request(URL, headers=headers)
with urllib.request.urlopen(req, timeout=20) as response:
    data = json.load(response)

if not isinstance(data, dict) or not data:
    raise SystemExit("CoinGecko returned no market data")

available = {k: v for k, v in data.items() if k in ASSETS and isinstance(v, dict) and "usd" in v}
if len(available) < 4:
    raise SystemExit(f"Only {len(available)} tracked assets returned; refusing to replace healthy cache")

payload = {
    "source": "CoinGecko",
    "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "assets": available,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUT.parent, delete=False) as tmp:
    json.dump(payload, tmp, separators=(",", ":"))
    tmp.write("\n")
    temp_name = tmp.name
Path(temp_name).replace(OUT)
print(f"Cached market data for {len(available)} assets at {OUT}")
