#!/usr/bin/env python3
"""News Watch entrypoint with a curated, domain-aware publisher catalog."""
import re
import news_watch as nw

PRIMARY = nw.PRIMARY_SOURCES | {
    "circle", "paxos", "paypal", "stripe", "fireblocks", "avalanche foundation",
    "polygon labs", "stellar development foundation", "hedera", "aptos labs",
    "arbitrum foundation", "optimism", "r3", "digital asset", "canton network",
    "world bank", "imf", "european commission", "esma", "fca", "finma",
    "bafin", "bank of korea", "korea financial services commission", "fsc korea",
    "monetary authority of singapore", "hkma", "abu dhabi global market", "adgm"
}
TRUSTED = nw.TRUSTED_MEDIA | {
    "axios", "bbc", "the economist", "marketwatch", "barrons", "associated press",
    "ap news", "nikkei asia", "south china morning post", "scmp"
}
SPECIALIST = nw.SPECIALIST_MEDIA | {
    "cointelegraph", "the defiant", "unchained", "cryptoslate", "blockworks",
    "ledger insights", "ledgerinsights", "coinpaper", "cryptodaily", "crypto daily",
    "tokenpost", "blocktelegraph", "block telegraph", "cryptonews", "cryptonews net",
    "cryptonews.net", "coinjournal", "beincrypto", "the block beats", "blockchain news",
    "finbold", "crowdfund insider", "asset servicing times", "securities finance times",
    "global banking and finance", "fintech global", "fintech magazine"
}
LOW = nw.LOW_TRUST_HINTS | {
    "pluang", "hokanews", "coincentral", "coingape", "ambcrypto", "newsbtc",
    "bitcoinist", "daily hodl", "cryptopotato"
}

ALIASES = {
    "coinpaper com": "coinpaper",
    "cryptodaily co uk": "cryptodaily",
    "crypto daily": "cryptodaily",
    "cryptonews net": "cryptonews",
    "tokenpost com": "tokenpost",
    "ledgerinsights com": "ledger insights",
    "blockworks co": "blockworks",
    "theblock co": "the block",
    "coindesk com": "coindesk",
    "reuters com": "reuters",
}

def normalize_source(name):
    s=(name or "").strip().lower()
    s=re.sub(r"^https?://(?:www\.)?", "", s)
    s=s.split("/",1)[0]
    s=re.sub(r"[^a-z0-9]+", " ", s).strip()
    parts=s.split()
    while parts and parts[-1] in {"com","org","net","io","co","news","finance","media","ai","us","uk","au"}:
        parts.pop()
    s=" ".join(parts)
    return ALIASES.get(s, s)

def _hit(value, keys):
    compact=value.replace(" ", "")
    for key in keys:
        k=normalize_source(key)
        if not k:
            continue
        kc=k.replace(" ", "")
        if value == k or compact == kc:
            return True
        if len(k) >= 5 and (k in value or value in k):
            return True
    return False

def source_tier(name):
    s=normalize_source(name)
    if _hit(s, PRIMARY): return "primary"
    if _hit(s, TRUSTED): return "trusted"
    if _hit(s, SPECIALIST): return "specialist"
    if _hit(s, nw.WIRE_SERVICES): return "wire"
    if _hit(s, LOW): return "low"
    return "unknown"

nw.normalize_source = normalize_source
nw.source_tier = source_tier

if __name__ == "__main__":
    nw.main()
