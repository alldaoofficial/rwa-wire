#!/usr/bin/env python3
import json
import math
import os
import tempfile
import urllib.request
from datetime import datetime, timezone, timedelta
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
    "reserve-rights-token": ("RSR", "Reserve Rights"),
    "origintrail": ("TRAC", "OriginTrail"),
    "origin-protocol": ("OGN", "Origin Protocol"),
    "truefi": ("TRU", "TrueFi"),
    "polytrade": ("TRADE", "Polytrade"),
    "propchain": ("PROPC", "Propchain"),
    "realio-network": ("RIO", "Realio Network"),
    "dusk-network": ("DUSK", "Dusk"),
    "chex-token": ("CHEX", "Chintai"),
    "landshare": ("LAND", "Landshare"),
    "boson-protocol": ("BOSON", "Boson Protocol"),
    "stobox-token": ("STBU", "Stobox"),
    "brickken": ("BKN", "Brickken"),
    "parcl": ("PRCL", "Parcl"),
    "tokenfi": ("TOKEN", "TokenFi"),
    "ix-swap": ("IXS", "IX Swap"),

}
OUT = Path("public/data/markets.json")
MAX_QUOTE_AGE = timedelta(hours=2)
MIN_COVERAGE = 4
HEADERS = {"Accept": "application/json", "User-Agent": "RWA-Wire/1.0"}

def get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def valid_quote(value, now):
    if not isinstance(value, dict):
        return False
    price = value.get("usd")
    change = value.get("usd_24h_change")
    updated = value.get("last_updated_at")
    if not isinstance(price, (int, float)) or isinstance(price, bool) or not math.isfinite(price) or price <= 0:
        return False
    if change is not None and (not isinstance(change, (int, float)) or isinstance(change, bool) or not math.isfinite(change)):
        return False
    if not isinstance(updated, (int, float)) or isinstance(updated, bool) or not math.isfinite(updated):
        return False
    age = now - datetime.fromtimestamp(updated, timezone.utc)
    return timedelta(0) <= age <= MAX_QUOTE_AGE

def coingecko():
    ids = list(ASSETS)
    url = "https://api.coingecko.com/api/v3/simple/price?ids=" + ",".join(ids) + "&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"
    headers = dict(HEADERS)
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key
    data = get_json(url, headers)
    now = datetime.now(timezone.utc)
    return {k:v for k,v in data.items() if k in ASSETS and valid_quote(v, now)}

def coinpaprika():
    tickers = get_json("https://api.coinpaprika.com/v1/tickers?quotes=USD")
    result = {}
    for key, (symbol, name) in ASSETS.items():
        candidates = [t for t in tickers if str(t.get("symbol","")).upper() == symbol.upper()]
        if not candidates:
            continue
        exact = [t for t in candidates if str(t.get("name","")).lower() == name.lower()]
        # Never resolve ambiguous tickers by symbol alone: they can represent unrelated assets.
        if len(exact) != 1:
            continue
        t = exact[0]
        q = (t.get("quotes") or {}).get("USD") or {}
        if not isinstance(q.get("price"), (int,float)) or isinstance(q.get("price"), bool) or not math.isfinite(q["price"]) or q["price"] <= 0:
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
    now = datetime.now(timezone.utc)
    return {key: value for key, value in result.items() if valid_quote(value, now)}

source = "CoinGecko"
try:
    available = coingecko()
except Exception as exc:
    print(f"CoinGecko unavailable: {exc}; trying CoinPaprika")
    available = {}

# Fill gaps in the CoinGecko universe instead of replacing all CoinGecko quotes.
# CoinPaprika matches are accepted only when both the ticker and full project name match.
if len(available) < len(ASSETS):
    try:
        fallback = coinpaprika()
        added = {key: quote for key, quote in fallback.items() if key not in available}
        available.update(added)
        if added:
            source = "CoinGecko + CoinPaprika" if len(available) > len(added) else "CoinPaprika"
        print(f"Market coverage: {len(available)}/{len(ASSETS)}; {len(added)} gaps filled from CoinPaprika")
    except Exception as exc:
        print(f"CoinPaprika fallback unavailable: {exc}; keeping verified CoinGecko quotes")


if len(available) < MIN_COVERAGE:
    raise SystemExit(f"Only {len(available)} fresh tracked assets returned; refusing to replace cache")

# Prevent a provider outage or degraded fallback from silently shrinking the usable universe.
# Compare against recent healthy cache only; old cache does not count as fresh coverage.
if OUT.exists():
    try:
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        previous_time = datetime.fromisoformat(previous["fetchedAt"].replace("Z", "+00:00"))
        if timedelta(0) <= datetime.now(timezone.utc) - previous_time <= MAX_QUOTE_AGE:
            previous_count = sum(valid_quote(value, datetime.now(timezone.utc)) for value in previous.get("assets", {}).values())
            if previous_count >= 8 and len(available) < max(MIN_COVERAGE, previous_count // 2):
                raise SystemExit(f"Provider coverage degraded from {previous_count} to {len(available)}; preserving recent cache")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Previous cache could not be compared: {exc}")

payload = {"source": source, "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"), "assets": available}
OUT.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUT.parent, delete=False) as tmp:
    json.dump(payload, tmp, separators=(",", ":"))
    tmp.write("\n")
    temp_name = tmp.name
Path(temp_name).replace(OUT)
missing = [f"{symbol} ({key})" for key, (symbol, _) in ASSETS.items() if key not in available]
print(f"Cached market data for {len(available)}/{len(ASSETS)} assets from {source} at {OUT}")
if missing:
    print("Unavailable tracked assets: " + ", ".join(missing))
else:
    print("All tracked assets have verified provider quotes")
