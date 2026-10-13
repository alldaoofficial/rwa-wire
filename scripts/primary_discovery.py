#!/usr/bin/env python3
"""Discover direct primary-source leads. Never invent copy or approve publication."""
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

import news_watch as nw

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = (
    {"name": "BIS", "url": "https://www.bis.org/doclist/all_pressrels.rss", "kind": "rss", "host": "bis.org"},
    {"name": "SEC", "url": "https://www.sec.gov/news/pressreleases.rss", "kind": "rss", "host": "sec.gov"},
    {"name": "ECB", "url": "https://www.ecb.europa.eu/rss/press.html", "kind": "rss", "host": "ecb.europa.eu"},
    {"name": "Ondo Finance", "url": "https://ondo.finance/blog", "kind": "html", "host": "ondo.finance", "prefix": "/blog/"},
    {"name": "Chainlink", "url": "https://chain.link/blog", "kind": "html", "host": "chain.link", "prefix": "/blog/"},
)
SIGNALS = ("tokenized", "tokenised", "tokenization", "tokenisation", "token securities",
           "token-securities", "deposit token", "distributed ledger", "digital bond",
           "onchain finance", "on-chain finance", "real-world assets", "real world assets")


def official(url, source):
    try:
        p = urllib.parse.urlparse(url)
        return (p.scheme == "https" and p.hostname in {source["host"], "www." + source["host"]}
                and not p.username and not p.password and p.port in (None, 443))
    except ValueError:
        return False


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, source):
        self.source = source

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not official(newurl, self.source):
            raise ValueError("non-official redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, source):
    if not official(url, source):
        raise ValueError("non-official source URL")
    request = urllib.request.Request(url, headers={"User-Agent": "RWA-Wire-Source-Discovery/1.0 (https://therwawire.com/contact/)", "Accept": "application/rss+xml, application/atom+xml, text/html"})
    with urllib.request.build_opener(Redirects(source)).open(request, timeout=15) as response:
        content = response.read(1_000_001)
        if len(content) > 1_000_000:
            raise ValueError("source exceeds size limit")
        return content


def date_value(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            d = parsedate_to_datetime(str(value))
        except (ValueError, TypeError):
            return None
    return d.replace(tzinfo=timezone.utc) if not d.tzinfo else d.astimezone(timezone.utc)


def rss_rows(raw, source):
    root = ET.fromstring(raw)
    def value(node, name):
        return next((x.text or "" for x in node if x.tag.rsplit("}", 1)[-1] == name), "")
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] not in {"item", "entry"}:
            continue
        url = value(item, "link")
        if not url:
            url = next((x.get("href", "") for x in item if x.tag.rsplit("}", 1)[-1] == "link" and x.get("rel", "alternate") == "alternate"), "")
        if not official(url, source):
            continue
        yield {"title": nw.clean(value(item, "title")), "url": url,
               "published": date_value(value(item, "pubDate") or value(item, "published") or value(item, "date") or value(item, "updated")),
               "summary": nw.clean(value(item, "description") or value(item, "summary"))}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.recent = []; self.in_recent = False; self.meta = {}; self.ld = []; self.script = None; self.published_time = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_recent:
                self.recent.append(a["href"])
        if tag == "meta":
            self.meta[a.get("property") or a.get("name")] = a.get("content", "")
        if tag == "time" and (a.get("itemprop") == "datePublished" or "pubdate" in a):
            self.published_time = a.get("datetime")
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.script = []

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        elif data.strip().lower() in {"recent posts", "all posts"}:
            self.in_recent = True

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            try:
                self.ld.append(json.loads("".join(self.script)))
            except ValueError:
                pass
            self.script = None


def ld_articles(value):
    if isinstance(value, list):
        for item in value:
            yield from ld_articles(item)
    elif isinstance(value, dict):
        if "datePublished" in value and ("headline" in value or "name" in value):
            yield value
        if "@graph" in value:
            yield from ld_articles(value["@graph"])
        if "mainEntity" in value:
            yield from ld_articles(value["mainEntity"])


def html_rows(raw, source, get=fetch, metrics=None):
    page = Page(); page.feed(raw.decode("utf-8", errors="replace"))
    urls = []
    for href in page.recent + page.links:
        url = urllib.parse.urljoin(source["url"], href)
        p = urllib.parse.urlparse(url)
        if official(url, source) and p.path.startswith(source["prefix"]) and p.path[len(source["prefix"]):].strip("/"):
            url = urllib.parse.urlunparse(p._replace(query="", fragment=""))
            if url not in urls:
                urls.append(url)
    # A small fixed per-publisher limit avoids crawling archives or hammering sites.
    for url in urls[:4]:
        try:
            article = Page(); article.feed(get(url, source).decode("utf-8", errors="replace"))
            ld = next(ld_articles(article.ld), {})
            yield {"title": nw.clean(ld.get("headline") or article.meta.get("og:title") or ld.get("name")),
                   "url": url, "published": date_value(ld.get("datePublished") or article.meta.get("article:published_time") or article.published_time),
                   "summary": nw.clean(ld.get("description") or article.meta.get("description") or article.meta.get("og:description"))}
        except Exception:
            if metrics is not None:
                metrics["article_access_errors"] += 1


def existing(root):
    titles, urls, slugs = [], set(), set()
    for folder in ("publish/inbox", "publish/candidates", "publish/approved", "publish/rejected", "publish/posted"):
        for path in (root / folder).glob("*.json"):
            try:
                d = json.loads(path.read_text()); titles.append(str(d.get("title", "")))
                urls.update(s["url"] for s in d.get("sources", []) if isinstance(s, dict) and isinstance(s.get("url"), str))
            except (ValueError, TypeError, KeyError):
                continue
    for path in (root / "src/content/articles").glob("*.mdx"):
        slugs.add(path.stem); titles.append(path.stem.replace("-", " "))
        match = re.search(r"^title:\s*(.+)$", path.read_text(), re.M)
        if match:
            titles.append(match[1].strip('"\''))
    return titles, urls, slugs


def run(root=ROOT, get=fetch, now=None, limit=2):
    now = now or datetime.now(timezone.utc)
    titles, known_urls, slugs = existing(root)
    metrics = Counter(); candidates = []; errors = []
    for source in SOURCES:
        try:
            raw = get(source["url"], source)
            rows = rss_rows(raw, source) if source["kind"] == "rss" else html_rows(raw, source, get, metrics)
            for row in rows:
                metrics["items"] += 1
                published = row["published"]
                if not published:
                    metrics["date_missing"] += 1; continue
                if published > now + timedelta(minutes=10) or now - published > timedelta(hours=48):
                    metrics["outside_window"] += 1; continue
                text = (row["title"] + " " + row["summary"]).lower()
                if not row["title"] or not any(term in text for term in SIGNALS) or any(term in text for term in nw.HARD_BLOCK):
                    metrics["irrelevant"] += 1; continue
                slug = nw.slugify(row["title"])
                if row["url"] in known_urls or slug in slugs or any(nw.slugify(row["title"]) == nw.slugify(title) for title in titles):
                    metrics["duplicate"] += 1; continue
                # Shared issuer/topic vocabulary is not evidence of the same event.
                # Preserve related leads for the source review's semantic judgment.
                row["relatedCoverageTitles"] = [title for title in titles if nw.same_story(row["title"], title)][:5]
                titles.append(row["title"]); known_urls.add(row["url"])
                candidates.append((published, source, row, slug))
            metrics["sources_ok"] += 1
        except Exception as exc:
            metrics["sources_failed"] += 1
            errors.append({"source": source["name"], "type": type(exc).__name__})
    written = []
    for published, source, row, slug in sorted(candidates, key=lambda x: x[0], reverse=True)[:limit]:
        d = {"title": row["title"], "description": "", "body": "", "why_it_matters": "",
             "pubDate": published.date().isoformat(), "category": "news",
             "tags": ["RWA", "Tokenization", "Primary Source"], "keyTakeaways": [],
             "sources": [{"name": source["name"], "url": row["url"]}],
             "newsWatch": {"score": 6, "priority": "important", "sourceTrust": "primary",
                           "discoveredAt": now.isoformat(), "sourcePublishedAt": published.isoformat(),
                           "discoveryMode": "direct-primary", "requiresSourceReview": True,
                           "relatedCoverageTitles": row.get("relatedCoverageTitles", []),
                           "autoPublishEligible": False, "contentStatus": "needs-source-enrichment"}}
        path = root / "publish/inbox" / (published.date().isoformat() + "-" + slug + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            metrics["existing_path"] += 1; continue
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
        written.append(str(path.relative_to(root)))
    result = {"checkedAt": now.isoformat(), "metrics": dict(metrics), "errors": errors, "written": written}
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
