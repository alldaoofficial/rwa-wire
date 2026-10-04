#!/usr/bin/env python3
"""Promote strong News Watch stories when independent high-quality sources confirm them."""
import json, pathlib, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import news_watch as nw

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "publish/news-watch-state.json"
INBOX = ROOT / "publish/inbox"

# Additional niche outlets that are useful for corroboration but are not strong enough
# to auto-publish a story on their own. Keep this deliberately conservative.
CONFIRMATION_SPECIALISTS = {
    "coinpaper", "cryptodaily", "crypto daily", "cointelegraph",
    "the cryptonomist", "blocktelegraph", "tokenpost", "bloomingbit",
    "financefeeds", "finextra", "ledger insights", "ledgerinsights",
    "global custodian", "globalcustodian", "banking dive", "pymnts",
    "markets media", "funds europe", "fintech futures"
}


def confirmation_tier(source):
    tier = nw.source_tier(source)
    if tier != "unknown":
        return tier
    normalized = nw.normalize_source(source)
    compact = normalized.replace(" ", "")
    for specialist in CONFIRMATION_SPECIALISTS:
        s = nw.normalize_source(specialist)
        if normalized == s or compact == s.replace(" ", ""):
            return "specialist"
    return tier


def google_results(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query + " when:3d",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    })
    root = ET.fromstring(nw.fetch(url))
    for x in root.findall(".//item"):
        title = nw.clean(x.findtext("title"))
        link = nw.clean(x.findtext("link"))
        desc = nw.clean(x.findtext("description"))
        source = title.rsplit(" - ", 1)[-1] if " - " in title else ""
        clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title
        try:
            published = parsedate_to_datetime(x.findtext("pubDate")).astimezone(timezone.utc)
        except Exception:
            published = datetime.now(timezone.utc)
        yield clean_title, link, desc, source, confirmation_tier(source), published


def independent(confirmations, original_source):
    original = nw.normalize_source(original_source)
    unique = []
    seen = set()
    for item in confirmations:
        source = nw.normalize_source(item[5])
        if not source or source == original or source in seen:
            continue
        seen.add(source)
        unique.append(item)
    return unique


def main():
    if not STATE.exists():
        return
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("lastResult") != "no-qualified-story":
        print("Confirmation pass skipped: News Watch already found a qualified story.")
        return

    watch = state.get("lastDiagnostics", {}).get("topWatchlist", [])
    watch = [x for x in watch if int(x.get("score", 0)) >= 7][:6]
    if not watch:
        print("Confirmation pass: no strong watchlist candidates.")
        return

    attempts = []
    for candidate in watch:
        original_title = candidate.get("title", "").strip()
        original_source = candidate.get("source", "").strip()
        score = int(candidate.get("score", 0))
        if not original_title:
            continue

        tokens = [t for t in nw.story_tokens(original_title) if len(t) >= 4]
        query = " ".join(sorted(tokens, key=len, reverse=True)[:8])
        matches = []
        try:
            for title, link, desc, source, trust, published in google_results(query):
                if trust not in {"primary", "trusted", "specialist"}:
                    continue
                if not nw.same_story(original_title, title):
                    continue
                matches.append((trust, published, title, link, desc, source))
        except Exception as exc:
            attempts.append({"title": original_title, "result": "search-error", "error": str(exc)[:120]})
            continue

        matches = independent(matches, original_source)
        high_trust = [m for m in matches if m[0] in {"primary", "trusted"}]
        specialists = [m for m in matches if m[0] == "specialist"]

        # One independent primary/trusted source is enough. Specialist-only promotion
        # is intentionally harder: score >= 9 AND two independent specialist outlets.
        if high_trust:
            confirmations = high_trust
            mode = "independent-high-trust-source"
        elif score >= 9 and len(specialists) >= 2:
            confirmations = specialists
            mode = "two-independent-specialist-sources"
        else:
            attempts.append({
                "title": original_title,
                "result": "unconfirmed",
                "highTrustMatches": len(high_trust),
                "specialistMatches": len(specialists)
            })
            continue

        rank = {"primary": 3, "trusted": 2, "specialist": 1}
        confirmations.sort(key=lambda r: (rank[r[0]], r[1]), reverse=True)
        trust, published, confirmed_title, link, desc, source = confirmations[0]
        band = "breaking" if score >= 9 and trust == "primary" else "important"
        summary = desc or f"{confirmed_title}. Independent sources confirm the development."
        if len(summary) > 420:
            summary = summary[:417].rstrip() + "..."
        why = "The development connects tokenized assets with institutional financial infrastructure and has been independently corroborated before entering the RWA Wire publishing pipeline."
        body = f"{summary}\n\n## Why it matters\n\n{why}\n\n## What to watch\n\nWatch for additional details on eligibility, custody, settlement and production use. RWA Wire will update coverage as the story develops."
        day = published.date().isoformat()
        slug = nw.slugify(confirmed_title)
        source_rows = [{"name": m[5], "url": m[3]} for m in confirmations[:2]]
        brief = {
            "title": confirmed_title,
            "description": summary,
            "why_it_matters": why,
            "pubDate": day,
            "category": "news",
            "tags": ["Tokenization", "Institutions", "News Watch"],
            "keyTakeaways": [summary, why],
            "body": body,
            "sources": source_rows,
            "newsWatch": {
                "score": score,
                "priority": band,
                "sourceTrust": trust,
                "discoveredAt": datetime.now(timezone.utc).isoformat(),
                "confirmationMode": mode,
                "originalDiscoveryTitle": original_title,
                "originalDiscoverySource": original_source,
                "confirmationSources": [m[5] for m in confirmations[:2]],
                "requiresSourceReview": True,
                "autoPublishEligible": True
            }
        }
        INBOX.mkdir(parents=True, exist_ok=True)
        path = INBOX / f"{day}-{slug}.json"
        if path.exists():
            attempts.append({"title": original_title, "result": "already-exists"})
            continue
        path.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        state["lastResult"] = "candidate-confirmed"
        state["lastCandidate"] = str(path.relative_to(ROOT))
        state["lastCandidatePriority"] = band
        state["lastConfirmation"] = {
            "original": original_source,
            "confirmedBy": [m[5] for m in confirmations[:2]],
            "trust": trust,
            "mode": mode
        }
        state["confirmationAttempts"] = attempts + [{
            "title": original_title,
            "result": "confirmed",
            "sources": [m[5] for m in confirmations[:2]],
            "mode": mode
        }]
        STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Confirmed watchlist story ({mode}): {path.relative_to(ROOT)}")
        return

    state["confirmationAttempts"] = attempts
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Confirmation pass: no watchlist story met high-trust or two-specialist confirmation rules.")


if __name__ == "__main__":
    main()
