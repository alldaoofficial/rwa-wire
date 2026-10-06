#!/usr/bin/env python3
"""Regression checks for curated News Watch publisher classification."""
import news_watch_v2 as catalog

CASES = {
    "https://www.coinpaper.com/story": "specialist",
    "CryptoDaily.co.uk": "specialist",
    "TokenPost.com": "specialist",
    "ledgerinsights.com": "specialist",
    "CoinNess": "specialist",
    "EnterpriseAM": "specialist",
    "Seoul Economic Daily": "trusted",
    "Reuters.com": "trusted",
    "Circle": "primary",
    "Pluang": "low",
    "Hokanews": "low",
    "Stocktwits": "low",
    "Bitget": "low",
    "Voice of Alexandria": "low",
}

for source, expected in CASES.items():
    actual = catalog.source_tier(source)
    assert actual == expected, f"{source}: expected {expected}, got {actual}"

print(f"Verified {len(CASES)} News Watch source classifications.")
