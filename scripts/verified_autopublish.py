"""Apply operator policy only to sealed source-reviewed RWA packages."""
import json
import pathlib
import re
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


def reconcile(root=ROOT):
    """Recover reviewed, already generated stories missed by event-only routing.

    Return only exact approved paths; no network or Telegram calls here. Existing
    receipts/rejections and every source-review/content check remain authoritative.
    """
    root = pathlib.Path(root).resolve()
    policy = json.loads((root / "publish/editorial-policy.json").read_text())
    paths = []
    for bp in sorted((root / "publish/inbox").glob("*.json")):
        try:
            brief = json.loads(bp.read_text())
            if not eligible(brief, policy):
                continue
            expected = expected_candidate(brief)
            cp = root / "publish/candidates" / (expected["id"] + ".json")
            slug = slugify(brief.get("slug") or brief["title"])
            article = (root / "src/content/articles" / (slug + ".mdx")).read_text()
            front, body = article.split("---", 2)[1:]
            if re.search(r"^draft:\s*true\s*$", front, re.M):
                continue
            if not re.search(r'^type:\s*"(?:NEWS|RESEARCH)"\s*$', front, re.M):
                continue
            fields = {"title": brief["title"], "pubDate": brief["pubDate"],
                      "category": brief.get("category", "news")}
            if any(f"{key}: {json.dumps(value, ensure_ascii=False)}" not in front
                   for key, value in fields.items()):
                continue
            # Never distribute an old brief after an English editorial correction.
            if body.split("\n\n---\n\n**Sources**", 1)[0].strip() != brief["body"].strip():
                continue
            if any(source["url"] not in body for source in brief["sources"]):
                continue
            approved = approve(str(bp.relative_to(root)), str(cp.relative_to(root)), root)
            if approved and approved not in paths:
                paths.append(approved)
        except (ValueError, KeyError, TypeError, OSError) as error:
            print(f"Automatic routing held for {bp.name}: {type(error).__name__}", file=sys.stderr)
    return paths


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--reconcile"]:
            print("\n".join(reconcile()))
            raise SystemExit(0)
        if len(sys.argv) != 3:
            raise ValueError("Usage: verified_autopublish.py brief candidate")
        print(approve(sys.argv[1], sys.argv[2]))
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
