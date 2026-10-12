#!/usr/bin/env python3
"""Queue and seal source-reviewed briefs; never fetch, generate or distribute here.

The evidence ledger is an audit record, not a mechanical proof of truth. Original
sources must be read by the reviewing agent/editor before using the seal command.
"""
import argparse
import hashlib
import ipaddress
import json
import pathlib
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
METHOD = "source-enrichment-v1"
REVIEWER = "RWA Wire Source Review"
CONTENT_FIELDS = ("title", "slug", "description", "why_it_matters", "body", "sources",
                  "pubDate", "category", "reviewCategory", "tags", "keyTakeaways",
                  "social", "caption", "readingTime", "heroImageAlt")


def digest(brief):
    content = {k: brief[k] for k in CONTENT_FIELDS if k in brief}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def timestamp(value):
    try:
        value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (ValueError, TypeError):
        return None


def direct_source(url):
    try:
        p = urlparse(str(url))
        host = (p.hostname or "").lower()
        if p.scheme != "https" or not host or p.username or p.password or p.port not in (None, 443):
            return False
        if host == "localhost" or "." not in host or host.endswith((".local", ".internal")):
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            pass
        if host in {"news.google.com", "www.news.google.com", "x.com", "twitter.com",
                    "www.youtube.com", "youtube.com", "t.me", "www.reddit.com", "reddit.com"}:
            return False
        if any(host == domain or host.endswith("." + domain) for domain in ("binance.com", "binance.bh", "binance.us")) and re.search(r"/(square|squ|sq)(/|$)", p.path, re.I):
            return False
        return bool(p.path.strip("/")) and not p.fragment
    except ValueError:
        return False


def review_reasons(brief, now=None, check_digest=True):
    now = now or datetime.now(timezone.utc)
    review = brief.get("sourceReview") or {}
    if not isinstance(review, dict):
        return ["invalid_source_review"]
    if review.get("method") != METHOD:
        return ["source_review_method_required"]
    reasons = []
    if review.get("status") != "verified" or review.get("reviewedBy") != REVIEWER:
        reasons.append("source_review_required")
    checked = timestamp(review.get("reviewedAt"))
    if not checked or not now - timedelta(days=7) <= checked <= now + timedelta(minutes=10):
        reasons.append("source_review_expired")
    if check_digest and review.get("contentSha256") != digest(brief):
        reasons.append("source_review_content_changed")
    for key in ("newsWatch", "cryptoWatch"):
        meta = brief.get(key) or {}
        if not isinstance(meta, dict):
            reasons.append("invalid_discovery_metadata")
            continue
        if meta.get("autoPublishEligible") is not False:
            if key in brief:
                reasons.append("source_review_cannot_auto_approve")
    sources = brief.get("sources") or []
    if not isinstance(sources, list) or any(not isinstance(s, dict) or not isinstance(s.get("url"), str) for s in sources):
        return reasons + ["invalid_source_evidence"]
    urls = {s.get("url") for s in sources}
    rows = review.get("sources")
    if not isinstance(rows, list) or not rows or len(rows) > 5:
        return reasons + ["source_evidence_required"]
    reviewed_urls = set()
    for row in rows:
        if not isinstance(row, dict):
            reasons.append("invalid_source_evidence")
            continue
        url = row.get("url")
        if not isinstance(url, str):
            reasons.append("invalid_source_evidence")
            continue
        reviewed_urls.add(url)
        date = timestamp(row.get("checkedAt"))
        try:
            published = datetime.strptime(str(row.get("publishedAt")), "%Y-%m-%d").date()
        except ValueError:
            published = None
        if not direct_source(url) or not date or not now - timedelta(days=7) <= date <= now + timedelta(minutes=10):
            reasons.append("invalid_source_evidence")
        if not published or published > now.date():
            reasons.append("source_date_required")
        if row.get("kind") not in {"primary", "news"} or row.get("access") != "full-text":
            reasons.append("full_source_required")
    if reviewed_urls != urls:
        reasons.append("source_evidence_mismatch")
    # Secondary reporting must have two distinct publishers, not a syndication mirror.
    if not any(isinstance(r, dict) and r.get("kind") == "primary" for r in rows):
        hosts = {urlparse(str(u)).hostname.removeprefix("www.") for u in reviewed_urls if direct_source(u)}
        if len(hosts) < 2 or review.get("independentReporting") is not True:
            reasons.append("independent_reporting_required")
    facts = review.get("facts")
    quotes = Counter()
    if not isinstance(facts, list) or not 3 <= len(facts) <= 8:
        reasons.append("three_supported_facts_required")
    else:
        claims = set()
        for fact in facts:
            if not isinstance(fact, dict):
                reasons.append("invalid_fact_evidence")
                continue
            claim = str(fact.get("claim", "")).strip()
            anchor = str(fact.get("anchor", "")).strip()
            url = fact.get("sourceUrl")
            if not isinstance(url, str):
                reasons.append("invalid_fact_evidence")
                continue
            claims.add(claim.lower())
            if not 6 <= len(claim.split()) <= 45 or not 1 <= len(anchor.split()) <= 8 or url not in urls:
                reasons.append("invalid_fact_evidence")
            quotes[url] += len(anchor.split())
        if len(claims) < 3:
            reasons.append("three_supported_facts_required")
        if any(count > 25 for count in quotes.values()):
            reasons.append("source_excerpts_too_long")
    body = str(brief.get("body", ""))
    # Remote source content is data, never executable MDX, JS or HTML.
    if re.search(r"[{}]|<\s*[!/a-zA-Z]|^\s*(import|export)\s|\]\(\s*(javascript|data):", body, re.M | re.I):
        reasons.append("unsafe_article_markup")
    return list(dict.fromkeys(reasons))


def seal(brief):
    from news_quality import quality_reasons
    reasons = review_reasons(brief, check_digest=False)
    if reasons:
        raise ValueError("Source review held: " + ", ".join(reasons))
    brief["sourceReview"]["contentSha256"] = digest(brief)
    reasons = quality_reasons(brief)
    if reasons:
        raise ValueError("Publication held: " + ", ".join(reasons))
    for key in ("newsWatch", "cryptoWatch"):
        if key in brief:
            brief[key]["contentStatus"] = "source-reviewed"
    return brief


def queue(root=ROOT, now=None, limit=2):
    """Return recent unresolved discoveries; no mutations or network requests."""
    from candidate_generator import slugify
    now = now or datetime.now(timezone.utc)
    rows = []
    for path in sorted((root / "publish/inbox").glob("*.json"), reverse=True):
        try:
            brief = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(brief, dict) or not ("newsWatch" in brief or "cryptoWatch" in brief):
                continue
            meta = brief.get("newsWatch") or brief.get("cryptoWatch") or {}
            if not isinstance(meta, dict):
                continue
            discovered = timestamp(meta.get("discoveredAt"))
            if not discovered or not now - timedelta(hours=48) <= discovered <= now + timedelta(minutes=10):
                continue
            review = brief.get("sourceReview") or {}
            if not isinstance(review, dict):
                continue
            if review.get("status") in {"verified", "rejected", "duplicate"}:
                continue
            last = timestamp(review.get("reviewedAt"))
            if review.get("status") == "held" and last and now - last < timedelta(hours=6):
                continue
            slug = slugify(brief.get("slug") or brief["title"])
            if (root / "src/content/articles" / (slug + ".mdx")).exists():
                continue
            rows.append({"path": str(path.relative_to(root)), "title": brief["title"],
                         "discoveredAt": discovered.isoformat(), "sources": brief.get("sources", [])})
        except (ValueError, TypeError, KeyError):
            continue
    rows.sort(key=lambda row: row["discoveredAt"], reverse=True)
    return rows[:limit]


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    q = sub.add_parser("queue")
    q.add_argument("--limit", type=int, default=2, choices=range(1, 6))
    s = sub.add_parser("seal")
    s.add_argument("brief")
    s.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "queue":
        print(json.dumps(queue(limit=args.limit), ensure_ascii=False, indent=2))
    else:
        brief = json.loads(pathlib.Path(args.brief).read_text(encoding="utf-8"))
        sealed = seal(brief)
        pathlib.Path(args.output).write_text(json.dumps(sealed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Source review sealed; no article or distribution created.")


if __name__ == "__main__":
    main()
