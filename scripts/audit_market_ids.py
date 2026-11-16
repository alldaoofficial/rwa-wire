#!/usr/bin/env python3
"""Read-only audit of the RWA Wire token catalog against CoinGecko's ID directory."""
import ast
import json
import urllib.request
from pathlib import Path

SOURCE = Path("scripts/update_market_data.py")
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
catalog = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ASSETS" for t in node.targets))
aliases = next((ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COINGECKO_IDS" for t in node.targets)), {})
req = urllib.request.Request("https://api.coingecko.com/api/v3/coins/list", headers={"User-Agent":"RWA-Wire/1.0","Accept":"application/json"})
with urllib.request.urlopen(req, timeout=45) as response:
    directory = json.load(response)
by_id = {coin["id"]: coin for coin in directory if isinstance(coin, dict) and coin.get("id")}
report = []
for key, (symbol, name) in catalog.items():
    provider_id = aliases.get(key, key)
    exact = by_id.get(provider_id)
    candidates = [coin for coin in directory if coin.get("symbol","").casefold() == symbol.casefold() and coin.get("name","").casefold() == name.casefold()]
    status = "id_and_symbol_match" if exact and exact.get("symbol","").casefold() == symbol.casefold() else "id_missing_or_symbol_mismatch"
    report.append({"configured_id":key,"provider_id":provider_id,"expected_symbol":symbol,"expected_name":name,"status":status,"directory_record":exact,"exact_name_symbol_candidates":candidates[:8]})
output = Path("market-id-audit.json")
output.write_text(json.dumps({"total":len(report),"records":report},indent=2)+"\n",encoding="utf-8")
print("Token directory audit:",len(report),"tracked")
for row in report:
    print(f"{row['status']}: {row['expected_symbol']} ({row['configured_id']})")
    if row["status"] != "id_and_symbol_match":
        print("  Candidate IDs (require human verification):",", ".join(c["id"] for c in row["exact_name_symbol_candidates"]) or "none")
print("Report saved to market-id-audit.json; no IDs changed automatically.")
