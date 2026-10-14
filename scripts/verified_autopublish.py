"""Apply operator policy only to sealed source-reviewed RWA packages."""
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from candidate_generator import slugify
from news_quality import quality_reasons

ROOT = pathlib.Path(__file__).resolve().parents[1]


def eligible(brief, policy):
    if policy.get("auto_publish_verified_rwa") is not True:
        return False
    if quality_reasons(brief):
        return False
    review = brief.get("sourceReview") or {}
    if review.get("method") != "source-enrichment-v1" or review.get("status") != "verified":
        return False
    watch = brief.get("newsWatch") or {}
    try:
        day = datetime.strptime(brief.get("pubDate", ""), "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        if not today - timedelta(days=3) <= day <= today:
            return False
        return int(watch.get("score", 0)) >= max(6, int(policy.get("minimum_rwa_score", 6)))
    except (ValueError, TypeError):
        return False


def expected_candidate(brief):
    slug = slugify(brief.get("slug") or brief["title"])
    pub = brief["pubDate"]
    category = brief.get("category", "news")
    url = f"https://therwawire.com/{category}/{slug}/"
    social = brief.get("social") or {}
    summary = str(social.get("summary") or brief["description"]).strip()
    hook = summary[:220].rstrip() + ("…" if len(summary) > 220 else "")
    label = brief.get("reviewCategory", category).upper()
    caption = brief.get("caption") or f"RWA WIRE // {label}\n\n{brief['title']}\n\n{hook}\n\nFull analysis →\n{url}"
    return {
        "id": f"{pub}-{slug}"[:55].rstrip("-"), "title": brief["title"],
        "category": label, "why_it_matters": brief["why_it_matters"],
        "article_url": url, "image_url": f"https://therwawire.com/images/news/{slug}.svg",
        "sources": brief["sources"], "caption": caption,
        "distribution": {"telegram": caption, "x": social.get("x") or f"{brief['title']}\n\n{hook}\n\n{url}",
                         "breaking": social.get("breaking") or f"RWA WIRE // {label}\n\n{brief['title']}\n\n{url}",
                         "summary": summary},
    }


def approve(brief_path, candidate_path, root=ROOT):
    root = pathlib.Path(root).resolve()
    bp, cp = (root / brief_path).resolve(), (root / candidate_path).resolve()
    if bp.parent != root / "publish/inbox" or cp.parent != root / "publish/candidates":
        raise ValueError("Unsupported package path")
    brief = json.loads(bp.read_text())
    candidate = json.loads(cp.read_text())
    policy = json.loads((root / "publish/editorial-policy.json").read_text())
    if not eligible(brief, policy):
        raise ValueError("Package requires manual review or source repair")
    expected = expected_candidate(brief)
    if any(candidate.get(key) != value for key, value in expected.items()):
        raise ValueError("Candidate copy differs from the source-reviewed package")
    if cp.stem != expected["id"]:
        raise ValueError("Candidate ID and filename differ")
    if (root / "publish/rejected" / cp.name).exists():
        raise ValueError("Rejected package cannot be auto-approved")
    if (root / "publish/posted" / cp.name).exists():
        return ""
    target = root / "publish/approved" / cp.name
    if target.exists():
        previous = json.loads(target.read_text())
        if any(previous.get(key) != value for key, value in expected.items()):
            raise ValueError("Existing approval differs; do not overwrite")
        return str(target.relative_to(root))
    candidate["automaticApproval"] = {"method": "verified-rwa-policy-v1", "sourceBrief": brief_path,
                                      "contentSha256": brief["sourceReview"]["contentSha256"],
                                      "approvedAt": datetime.now(timezone.utc).isoformat()}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    return str(target.relative_to(root))


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise ValueError("Usage: verified_autopublish.py brief candidate")
        print(approve(sys.argv[1], sys.argv[2]))
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
