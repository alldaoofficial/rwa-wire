#!/usr/bin/env python3
"""Promote strong News Watch stories only when an independent high-trust source confirms them."""
import json, pathlib, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import news_watch as nw

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "publish/news-watch-state.json"
INBOX = ROOT / "publish/inbox"


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
        yield clean_title, link, desc, source, nw.source_tier(source), published


def main():
    if not STATE.exists():
        return
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("lastResult") != "no-qualified-story":
        print("Confirmation pass skipped: News Watch already found a qualified story.")
        return

    watch = state.get("lastDiagnostics", {}).get("topWatchlist", [])
    # Only spend confirmation requests on genuinely strong candidates.
    watch = [x for x in watch if int(x.get("score", 0)) >= 7][:5]
    if not watch:
        print("Confirmation pass: no strong watchlist candidates.")
        return

    attempts = []
    for candidate in watch:
        original_title = candidate.get("title", "").strip()
        original_source = candidate.get("source", "").strip()
        if not original_title:
            continue

        # Search a compact set of distinctive headline terms instead of trusting the first publisher.
        tokens = [t for t in nw.story_tokens(original_title) if len(t) >= 4]
        query = " ".join(sorted(tokens, key=len, reverse=True)[:8])
        confirmations = []
        try:
            for title, link, desc, source, trust, published in google_results(query):
                if trust not in {"primary", "trusted"}:
                    continue
                if nw.normalize_source(source) == nw.normalize_source(original_source):
                    continue
                if not nw.same_story(original_title, title):
                    continue
                confirmations.append((trust, published, title, link, desc, source))
        except Exception as exc:
            attempts.append({"title": original_title, "result": "search-error", "error": str(exc)[:120]})
            continue

        if not confirmations:
            attempts.append({"title": original_title, "result": "unconfirmed"})
            continue

        confirmations.sort(key=lambda r: ((2 if r[0] == "primary" else 1), r[1]), reverse=True)
        trust, published, confirmed_title, link, desc, source = confirmations[0]
        score = int(candidate.get("score", 0))
        band = "breaking" if score >= 9 and trust == "primary" else "important"
        summary = desc or f"{confirmed_title}. A high-trust source independently confirms the development."
        if len(summary) > 420:
            summary = summary[:417].rstrip() + "..."
        why = "The development connects tokenized assets with institutional financial infrastructure and has now been independently confirmed by a primary or trusted source."
        body = f"{summary}\n\n## Why it matters\n\n{why}\n\n## What to watch\n\nWatch for additional details on eligibility, custody, settlement and production use. RWA Wire will update coverage as the story develops."
        day = published.date().isoformat()
        slug = nw.slugify(confirmed_title)
        brief = {
            "title": confirmed_title,
            "description": summary,
            "why_it_matters": why,
            "pubDate": day,
            "category": "news",
            "tags": ["Tokenization", "Institutions", "News Watch"],
            "keyTakeaways": [summary, why],
            "body": body,
            "sources": [
                {"name": source, "url": link},
                {"name": original_source or "Discovery source", "url": ""}
            ],
            "newsWatch": {
                "score": score,
                "priority": band,
                "sourceTrust": trust,
                "discoveredAt": datetime.now(timezone.utc).isoformat(),
                "confirmationMode": "independent-high-trust-source",
                "originalDiscoveryTitle": original_title,
                "originalDiscoverySource": original_source,
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
        state["lastConfirmation"] = {"original": original_source, "confirmedBy": source, "trust": trust}
        state["confirmationAttempts"] = attempts + [{"title": original_title, "result": "confirmed", "source": source, "trust": trust}]
        STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Confirmed watchlist story via {source} ({trust}): {path.relative_to(ROOT)}")
        return

    state["confirmationAttempts"] = attempts
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Confirmation pass: no watchlist story received independent primary/trusted confirmation.")


if __name__ == "__main__":
    main()
