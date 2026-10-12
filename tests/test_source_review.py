import copy
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import source_review as sr
import news_quality as quality
import news_watch
import news_watch_v2 as catalog
from test_news_quality import good


def reviewed():
    d = good()
    now = datetime.now(timezone.utc).isoformat()
    d["newsWatch"] = {"autoPublishEligible": False, "discoveredAt": now}
    url = d["sources"][0]["url"]
    d["sourceReview"] = {
        "method": sr.METHOD, "status": "verified", "reviewedBy": sr.REVIEWER,
        "reviewedAt": now,
        "sources": [{"url": url, "publishedAt": datetime.now(timezone.utc).date().isoformat(),
                     "checkedAt": now, "kind": "primary", "access": "full-text"}],
        "facts": [
            {"claim": "The fictional trial serves approved corporate customers at two branches.", "sourceUrl": url, "anchor": "approved corporate customers"},
            {"claim": "The fictional product represents euro deposit balances at the bank.", "sourceUrl": url, "anchor": "euro deposit balances"},
            {"claim": "The fictional trial runs only during normal banking hours.", "sourceUrl": url, "anchor": "normal banking hours"},
        ],
    }
    return d


class SourceReviewTests(unittest.TestCase):
    def test_supported_review_passes_without_auto_approval(self):
        d = sr.seal(reviewed())
        self.assertEqual(quality.quality_reasons(d), [])
        self.assertFalse(d["newsWatch"]["autoPublishEligible"])
        self.assertEqual(d["newsWatch"]["contentStatus"], "source-reviewed")

    def test_modified_copy_needs_new_review(self):
        original = sr.seal(reviewed())
        for field in ("title", "description", "body", "why_it_matters", "pubDate", "caption"):
            d = copy.deepcopy(original); d[field] = str(d.get(field, "")) + " modified"
            self.assertIn("source_review_content_changed", quality.quality_reasons(d))
        d = copy.deepcopy(original); d["sources"][0]["url"] += "-different"
        self.assertIn("source_evidence_mismatch", quality.quality_reasons(d))

    def test_no_flag_only_bypass(self):
        d = good(); d["newsWatch"] = {"autoPublishEligible": False}
        d["sourceReview"] = {"status": "verified", "reviewedBy": sr.REVIEWER}
        self.assertIn("source_review_method_required", quality.quality_reasons(d))

    def test_stale_or_future_review_held(self):
        for offset in (-8, 1):
            d = reviewed(); d["sourceReview"]["reviewedAt"] = (datetime.now(timezone.utc)+timedelta(days=offset)).isoformat()
            with self.assertRaisesRegex(ValueError, "source_review_expired"):
                sr.seal(d)

    def test_snippet_and_missing_fact_held(self):
        d = reviewed(); d["sourceReview"]["sources"][0]["access"] = "snippet"
        with self.assertRaisesRegex(ValueError, "full_source_required"): sr.seal(d)
        d = reviewed(); d["sourceReview"]["facts"].pop()
        with self.assertRaisesRegex(ValueError, "three_supported_facts_required"): sr.seal(d)

    def test_secondary_source_needs_distinct_reporting(self):
        d = reviewed(); d["sourceReview"]["sources"][0]["kind"] = "news"
        with self.assertRaisesRegex(ValueError, "independent_reporting_required"): sr.seal(d)
        d["sources"].append({"name": "Second publisher", "url": "https://other.example/story"})
        d["sourceReview"]["sources"].append(dict(d["sourceReview"]["sources"][0], url="https://other.example/story"))
        d["sourceReview"]["independentReporting"] = True
        self.assertEqual(quality.quality_reasons(sr.seal(d)), [])

    def test_discovery_and_community_urls_rejected(self):
        for url in ("https://news.google.com/rss/articles/test", "https://www.binance.com/en/square/post/123", "https://127.0.0.1/story", "https://user:pass@example.com/story", "https://example.com/", "http://example.com/story"):
            self.assertFalse(sr.direct_source(url), url)
        self.assertTrue(sr.direct_source("https://www.binance.com/en/support/announcement/detail/test"))
        self.assertEqual(catalog.source_tier("Binance Square"), "low")

    def test_executable_source_content_rejected(self):
        for unsafe in ("<script>alert(1)</script>", "{process.env.SECRET}", "\nimport X from 'module'", "[click](javascript:alert(1))"):
            d = reviewed(); d["body"] += "\n" + unsafe
            with self.assertRaisesRegex(ValueError, "unsafe_article_markup"): sr.seal(d)

    def test_review_cannot_grant_distribution_approval(self):
        d = reviewed(); d["newsWatch"]["autoPublishEligible"] = True
        with self.assertRaisesRegex(ValueError, "source_review_cannot_auto_approve"): sr.seal(d)

    def test_copyright_excerpt_budget(self):
        d = reviewed(); facts = d["sourceReview"]["facts"]
        for fact in facts: fact["anchor"] = "one two three four five six seven eight"
        facts.append(dict(facts[0], claim="A fourth distinct fictional claim is documented by the issuer."))
        with self.assertRaisesRegex(ValueError, "source_excerpts_too_long"): sr.seal(d)

    def test_queue_ignores_old_reviewed_published_and_retrying_leads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); inbox = root/"publish/inbox"; inbox.mkdir(parents=True)
            now = datetime.now(timezone.utc)
            for i in range(6):
                d = reviewed(); d["title"] += f" {i}"; d.pop("sourceReview")
                if i == 1: d["newsWatch"]["discoveredAt"] = (now-timedelta(days=3)).isoformat()
                if i == 2: d["sourceReview"] = {"status": "verified"}
                if i == 3:
                    p = root/"src/content/articles"; p.mkdir(parents=True)
                    from candidate_generator import slugify
                    (p/(slugify(d["title"])+".mdx")).write_text("published")
                if i == 4: d["sourceReview"] = {"status": "held", "reviewedAt": now.isoformat()}
                if i == 5: d["sourceReview"] = {"status": "duplicate"}
                (inbox/f"{i}.json").write_text(json.dumps(d))
            self.assertEqual([x["path"] for x in sr.queue(root, now)], ["publish/inbox/0.json"])

    def test_community_aggregate_never_becomes_discovery(self):
        from email.utils import format_datetime
        now = format_datetime(datetime.now(timezone.utc))
        rss = ('<rss><channel><item><title>#tokenizedsecurities Community Insights &amp; Market Sentiment | Binance Square - Binance</title><link>https://news.google.com/rss/articles/test</link><guid>test</guid><description>tokenized securities institutions settlement bank</description><pubDate>'+now+'</pubDate></item></channel></rss>').encode()
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); (root/"publish").mkdir()
            with patch.object(news_watch, "ROOT", root), patch.object(news_watch, "STATE", root/"publish/state.json"), patch.object(news_watch, "INBOX", root/"publish/inbox"), patch.object(news_watch, "QUERIES", ["test"]), patch.object(news_watch, "fetch", return_value=rss):
                news_watch.main()
            self.assertFalse((root/"publish/inbox").exists())
            self.assertEqual(json.loads((root/"publish/state.json").read_text())["lastDiagnostics"]["rejections"]["community_feed"], 1)


if __name__ == "__main__":
    unittest.main()
