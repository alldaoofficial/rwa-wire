#!/usr/bin/env python3
"""Conservative pre-publication checks. Passing is not a fact-check."""
import argparse
import html
import json
import os
import re
from urllib.parse import urlparse

FILLER = (
    "rwa wire is tracking the development", "the development connects tokenized assets",
    "watch for additional details on eligibility", "rwa wire will update coverage",
    "has been independently corroborated before entering", "a new institutional tokenization development",
    "this is a market-wide signal", "broader crypto liquidity and institutional risk appetite",
)
STOP = set("a an the and or of to in on for as with its is are was were by from at this that it be has have will can could would".split())

def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value or "")))).strip()

def tokens(value):
    return {w for w in re.findall(r"[a-z0-9]+", clean(value).lower()) if len(w) > 2 and w not in STOP}

def repeats(a, b):
    aa, bb = tokens(a), tokens(b)
    return bool(aa and bb and len(aa & bb) / min(len(aa), len(bb)) >= .85 and len(bb - aa) < 4)

def quality_reasons(d):
    reasons = []
    title, summary, why, body = (clean(d.get(k)) for k in ("title", "description", "why_it_matters", "body"))
    if not title:
        reasons.append("missing_title")
    if len(summary.split()) < 18 or len(tokens(summary) - tokens(title)) < 6 or repeats(title, summary):
        reasons.append("summary_adds_too_little")
    if len(why.split()) < 18 or repeats(summary, why) or len(tokens(why) - tokens(title + " " + summary)) < 5:
        reasons.append("missing_specific_relevance")
    if len(body.split()) < 90:
        reasons.append("insufficient_reported_detail")
    fields = [summary, why, body] + [clean(x) for x in (d.get("keyTakeaways") or [])]
    social = d.get("social") or {}
    fields += [clean(social.get(k)) for k in ("summary", "x", "breaking")]
    fields += [clean(d.get("caption"))]
    if any(phrase in text.lower() for text in fields for phrase in FILLER):
        reasons.append("boilerplate")
    sources = d.get("sources")
    if not isinstance(sources, list) or not sources:
        reasons.append("missing_source")
    else:
        for source in sources:
            parsed = urlparse(str(source.get("url", ""))) if isinstance(source, dict) else urlparse("")
            if parsed.scheme != "https" or not parsed.hostname or not clean(source.get("name")):
                reasons.append("invalid_source")
                break
            if parsed.hostname.lower() in {"news.google.com", "www.news.google.com"}:
                reasons.append("unresolved_discovery_source")
                break
    # RSS discovery and headline corroboration do not establish source facts.
    if "newsWatch" in d or "cryptoWatch" in d:
        review = d.get("sourceReview") or {}
        if review.get("status") != "verified" or not clean(review.get("reviewedBy")):
            reasons.append("source_review_required")
    return list(dict.fromkeys(reasons))

def require_quality(d):
    reasons = quality_reasons(d)
    if reasons:
        raise ValueError("Publication held: " + ", ".join(reasons))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("brief")
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()
    with open(args.brief, encoding="utf-8") as handle:
        reasons = quality_reasons(json.load(handle))
    print("Publication held: " + ", ".join(reasons) if reasons else "Content quality checks passed.")
    if args.github_output:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write("eligible=" + ("false" if reasons else "true") + "\n")
        return
    raise SystemExit(1 if reasons else 0)

if __name__ == "__main__":
    main()
