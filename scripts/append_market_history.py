#!/usr/bin/env python3
"""Append verified market snapshots for historical charts (maximum 30 days)."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

SOURCE = Path("public/data/markets.json")
TARGET = Path("public/data/market-history.json")
now = datetime.now(timezone.utc)
cache = json.loads(SOURCE.read_text(encoding="utf-8"))
timestamp = datetime.fromisoformat(cache["fetchedAt"].replace("Z", "+00:00"))
if timestamp > now or now - timestamp > timedelta(hours=2):
    print("Market cache is stale; skipping history append")
    raise SystemExit(0)
history = {"schema": 1, "points": []}
if TARGET.exists():
    history = json.loads(TARGET.read_text(encoding="utf-8"))
points = history.get("points", [])
if points:
    last = datetime.fromisoformat(points[-1]["at"].replace("Z", "+00:00"))
    if timestamp <= last or timestamp - last < timedelta(hours=6):
        print("No new six-hour snapshot needed")
        raise SystemExit(0)
prices = {
    key: round(value["usd"], 10)
    for key, value in cache.get("assets", {}).items()
    if isinstance(value, dict) and isinstance(value.get("usd"), (int, float))
    and not isinstance(value.get("usd"), bool) and math.isfinite(value["usd"]) and value["usd"] > 0
}
if len(prices) < 4:
    raise SystemExit("Too few valid prices for history; keeping prior data")
points.append({"at": timestamp.isoformat().replace("+00:00", "Z"), "prices": prices})
cutoff = now - timedelta(days=30)
points = [point for point in points if datetime.fromisoformat(point["at"].replace("Z", "+00:00")) >= cutoff]
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps({"schema": 1, "points": points}, separators=(",", ":")) + "\n", encoding="utf-8")
print(f"Recorded {len(prices)} prices; {len(points)} historical snapshots retained")
