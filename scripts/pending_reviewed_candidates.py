#!/usr/bin/env python3
"""Select one fully reviewed, quality-passing brief awaiting candidate generation.

Read-only: never edits a review, generates a story or changes editorial policy.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from candidate_generator import slugify
from news_quality import quality_reasons


def pending(root=ROOT):
    rows = []
    for path in (root / "publish/inbox").glob("*.json"):
        try:
            brief = json.loads(path.read_text(encoding="utf-8"))
            review = brief.get("sourceReview") or {}
            if review.get("status") != "verified" or quality_reasons(brief):
                continue
            slug = slugify(brief.get("slug") or brief["title"])
            candidate_id = f'{brief["pubDate"]}-{slug}'[:55].rstrip("-")
            if (root / "publish/candidates" / (candidate_id + ".json")).exists():
                continue
            rows.append((brief.get("pubDate", ""), path))
        except (ValueError, KeyError, TypeError, OSError):
            continue
    return sorted(rows, key=lambda row: (row[0], row[1].name), reverse=True)


if __name__ == "__main__":
    queue = pending()
    if queue:
        print(queue[0][1].relative_to(ROOT))
    else:
        print("No fully reviewed candidate backlog", file=sys.stderr)
