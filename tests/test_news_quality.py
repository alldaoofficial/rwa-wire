import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import news_quality as q
import candidate_generator as generator
import news_watch
import news_watch_confirm
import crypto_market_watch

def good():
    return {
        "title": "Example Bank begins a tokenized deposit pilot",
        "description": "The trial lets approved corporate customers transfer euro deposit balances between two branches, with transactions recorded on a restricted ledger during normal banking hours.",
        "why_it_matters": "Connecting both branches gives treasury teams a way to test internal cash transfers without moving balances into a separate investment product, while access remains limited to participating customers.",
        "body": """Example Bank has begun a trial for approved corporate customers transferring euro deposit balances between two branches. The fictional example uses a restricted ledger and operates during normal banking hours. Participants retain a claim on the issuing bank rather than receiving shares in an investment fund.

The trial covers internal cash transfers. It does not establish that other banks can receive the balances, that transfers run overnight or that the service is available to all depositors. Those limits distinguish the scope of this test from a commercial payments network.

Connecting the branches allows treasury teams to evaluate a specific cash-management process. Evidence of recurring customer use would be needed to assess whether the trial supports a wider rollout.""",
        "sources": [{"name": "Example Bank", "url": "https://example.com/pilot"}],
        "category": "news",
    }

class QualityTests(unittest.TestCase):
    def test_discovery_retains_lead_without_inventing_article(self):
        from datetime import datetime, timezone
        from email.utils import format_datetime
        now = format_datetime(datetime.now(timezone.utc))
        rss = ('<rss><channel><item><title>Example Bank launches tokenized deposits settlement pilot - Reuters</title>'
               '<link>https://news.google.com/rss/articles/example</link><guid>test</guid>'
               '<description>Example Bank launches tokenized deposits settlement pilot Reuters</description>'
               '<pubDate>' + now + '</pubDate></item></channel></rss>').encode()
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); (root/'publish').mkdir()
            with patch.object(news_watch,'ROOT',root), patch.object(news_watch,'STATE',root/'publish/state.json'), patch.object(news_watch,'INBOX',root/'publish/inbox'), patch.object(news_watch,'fetch',return_value=rss), patch.object(news_watch,'QUERIES',['test']):
                news_watch.main()
            brief=json.loads(next((root/'publish/inbox').glob('*.json')).read_text())
            self.assertFalse(brief['newsWatch']['autoPublishEligible'])
            self.assertEqual(brief['why_it_matters'],'')
            self.assertNotIn('rwa wire is tracking',brief['body'].lower())
            self.assertIn('source_review_required',q.quality_reasons(brief))

    def test_independent_confirmation_still_retains_only_a_lead(self):
        from datetime import datetime, timezone
        title='Example Bank launches tokenized deposits settlement pilot'
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp); state=root/'state.json'
            state.write_text(json.dumps({'lastResult':'no-qualified-story','lastDiagnostics':{'topWatchlist':[{'title':title,'source':'Finextra','score':10}]}}))
            matches=[(title,'https://news.google.com/rss/articles/example',title,'Reuters','trusted',datetime.now(timezone.utc))]
            with patch.object(news_watch_confirm,'ROOT',root), patch.object(news_watch_confirm,'STATE',state), patch.object(news_watch_confirm,'INBOX',root/'inbox'), patch.object(news_watch_confirm,'google_results',return_value=iter(matches)):
                news_watch_confirm.main()
            brief=json.loads(next((root/'inbox').glob('*.json')).read_text())
            self.assertFalse(brief['newsWatch']['autoPublishEligible'])
            self.assertEqual(brief['why_it_matters'],'')
            self.assertIn('source_review_required',q.quality_reasons(brief))

    def test_substantive_brief_passes(self):
        self.assertEqual(q.quality_reasons(good()), [])
        generator.validate(good())

    def test_headline_with_publisher_suffix_held(self):
        d = good(); d["description"] = d["title"] + ". Example Bank"
        self.assertIn("summary_adds_too_little", q.quality_reasons(d))

    def test_headline_with_old_filler_held(self):
        d = good(); d["description"] = d["title"] + ". RWA Wire is tracking the development for its relevance to institutional tokenization."
        self.assertIn("boilerplate", q.quality_reasons(d))

    def test_generic_relevance_held(self):
        d = good(); d["why_it_matters"] = "The development connects tokenized assets with institutional financial infrastructure, showing how onchain instruments are moving into practical market workflows."
        self.assertIn("boilerplate", q.quality_reasons(d))

    def test_repeat_summary_as_relevance_held(self):
        d = good(); d["why_it_matters"] = d["description"]
        self.assertIn("missing_specific_relevance", q.quality_reasons(d))

    def test_short_body_held(self):
        d = good(); d["body"] = d["description"]
        self.assertIn("insufficient_reported_detail", q.quality_reasons(d))

    def test_unresolved_google_news_held(self):
        d = good(); d["sources"][0]["url"] = "https://news.google.com/rss/articles/example"
        self.assertIn("unresolved_discovery_source", q.quality_reasons(d))

    def test_missing_or_invalid_sources(self):
        for sources in ([], [{"name": "Bank", "url": "http://example.com"}], [{"name": "", "url": "https://example.com"}]):
            d = good(); d["sources"] = sources
            self.assertTrue(q.quality_reasons(d))

    def test_headline_confirmation_is_not_source_review(self):
        d = good(); d["newsWatch"] = {"confirmationMode": "independent-high-trust-source", "autoPublishEligible": True}
        self.assertIn("source_review_required", q.quality_reasons(d))

    def test_verified_source_review_can_pass(self):
        d = good(); d["newsWatch"] = {"autoPublishEligible": False}
        d["sourceReview"] = {"status": "verified", "reviewedBy": "Editor"}
        self.assertEqual(q.quality_reasons(d), [])

    def test_review_cannot_override_bad_content(self):
        d = good(); d["newsWatch"] = {}; d["description"] = d["title"]
        d["sourceReview"] = {"status": "verified", "reviewedBy": "Editor"}
        self.assertIn("summary_adds_too_little", q.quality_reasons(d))

    def test_social_overrides_are_checked(self):
        d = good(); d["social"] = {"summary": "RWA Wire is tracking the development for its relevance to institutional tokenization."}
        self.assertIn("boilerplate", q.quality_reasons(d))

    def test_direct_generator_cannot_bypass_gate(self):
        d = good(); d["description"] = d["title"]
        with self.assertRaisesRegex(ValueError, "Publication held"):
            generator.validate(d)

    def test_workflow_hold_is_success_without_eligible_output(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp); d = good(); d["description"] = d["title"]
            (p/"brief.json").write_text(json.dumps(d))
            env = dict(os.environ, GITHUB_OUTPUT=str(p/"output"))
            result = subprocess.run([sys.executable, q.__file__, str(p/"brief.json"), "--github-output"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual((p/"output").read_text(), "eligible=false\n")

    def test_valid_generator_keeps_body_and_computes_reading_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp); original = (generator.ROOT, generator.ARTICLES, generator.IMAGES, generator.CANDIDATES, sys.argv)
            try:
                generator.ROOT=root; generator.ARTICLES=root/"articles"; generator.IMAGES=root/"images"; generator.CANDIDATES=root/"candidates"
                d=good(); (root/"brief.json").write_text(json.dumps(d)); sys.argv=["candidate_generator.py",str(root/"brief.json")]
                generator.main()
                article=next(generator.ARTICLES.glob("*.mdx")).read_text()
                self.assertIn(d["body"],article)
                self.assertNotIn("What would strengthen the signal",article)
                self.assertIn('readingTime: "1 min read"',article)
            finally:
                generator.ROOT, generator.ARTICLES, generator.IMAGES, generator.CANDIDATES, sys.argv = original

if __name__ == "__main__":
    unittest.main()
