import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import primary_discovery as primary
import distribution_audit as distribution
import editorial_approval as editorial
import news_quality


def feed(title="Example Bank launches tokenized deposit pilot", days=0, url="https://www.bis.org/press/test.htm"):
    date=format_datetime(datetime.now(timezone.utc)-timedelta(days=days))
    return f'<rss><channel><item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate></item></channel></rss>'.encode()


class PrimaryTests(unittest.TestCase):
    def test_direct_lead_has_link_and_cannot_publish_without_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            with patch.object(primary,"SOURCES",[primary.SOURCES[0]]):
                result=primary.run(root,get=lambda *args: feed())
            self.assertEqual(len(result["written"]),1)
            d=json.loads((root/result["written"][0]).read_text())
            self.assertEqual(d["sources"][0]["url"],"https://www.bis.org/press/test.htm")
            self.assertEqual(d["body"],"")
            self.assertFalse(d["newsWatch"]["autoPublishEligible"])
            self.assertIn("source_review_required",news_quality.quality_reasons(d))

    def test_stale_future_irrelevant_and_foreign_links_do_not_enqueue(self):
        for data in (feed(days=3),feed(days=-1),feed(title="Bank announces annual meeting"),feed(url="https://bad.example/news")):
            with tempfile.TemporaryDirectory() as tmp, patch.object(primary,"SOURCES",[primary.SOURCES[0]]):
                self.assertFalse(primary.run(pathlib.Path(tmp),get=lambda *args:data)["written"])

    def test_semantic_duplicate_and_existing_link_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(primary,"SOURCES",[primary.SOURCES[0]]):
            root=pathlib.Path(tmp);primary.run(root,get=lambda *args:feed())
            self.assertFalse(primary.run(root,get=lambda *args:feed(title="Example Bank introduces tokenized deposit pilot"))["written"])

    def test_related_new_milestone_reaches_review_instead_of_keyword_rejection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(primary,"SOURCES",[primary.SOURCES[0]]):
            root=pathlib.Path(tmp);primary.run(root,get=lambda *args:feed())
            result=primary.run(root,get=lambda *args:feed(title="Example Bank expands tokenized deposit pilot to corporate customers",url="https://www.bis.org/press/next.htm"))
            self.assertEqual(len(result["written"]),1)
            d=json.loads((root/result["written"][0]).read_text())
            self.assertTrue(d["newsWatch"]["relatedCoverageTitles"])
            self.assertFalse(d["newsWatch"]["autoPublishEligible"])

    def test_atom_and_bad_dates(self):
        data=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Tokenized bonds</title><link href="https://www.bis.org/press/test.htm"/><published>2026-10-13T03:00:00Z</published></entry></feed>'
        row=list(primary.rss_rows(data,primary.SOURCES[0]))[0]
        self.assertEqual(row["published"].year,2026)
        self.assertIsNone(primary.date_value("not-a-date"))

    def test_official_hostname_and_redirect_boundaries(self):
        source=primary.SOURCES[0]
        for url in ("https://bis.org.evil.example/story","http://www.bis.org/press/a","https://secret@www.bis.org/press/a","https://www.bis.org:8000/press/a"):
            self.assertFalse(primary.official(url,source))
        with self.assertRaisesRegex(ValueError,"non-official redirect"):
            primary.Redirects(source).redirect_request(None,None,302,"",{},"https://evil.example/story")

    def test_full_page_metadata_not_featured_archive_gets_priority(self):
        source=primary.SOURCES[4]
        listing=b'<a href="/blog/old">Old featured</a><h2>Recent posts</h2><a href="/blog/new">New post</a>'
        def get(url,source):
            return ('<script type="application/ld+json">'+json.dumps({"@type":"Article","headline":"Tokenized bank bonds", "datePublished":datetime.now(timezone.utc).isoformat(),"description":"A bank bond pilot"})+'</script>').encode()
        rows=list(primary.html_rows(listing,source,get))
        self.assertEqual(rows[0]["url"],"https://chain.link/blog/new")
        self.assertEqual(rows[0]["title"],"Tokenized bank bonds")

    def test_blocked_publisher_is_diagnostic_not_fake_story(self):
        def blocked(*args):raise TimeoutError("unavailable")
        with tempfile.TemporaryDirectory() as tmp, patch.object(primary,"SOURCES",[primary.SOURCES[0]]):
            d=primary.run(pathlib.Path(tmp),get=blocked)
        self.assertFalse(d["written"])
        self.assertEqual(d["metrics"]["sources_failed"],1)


class DistributionTests(unittest.TestCase):
    def test_approval_publication_and_paused_x_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);folder=root/"publish/candidates";folder.mkdir(parents=True)
            (root/"publish/channel-config.json").write_text('{"x_enabled":false}')
            (folder/"id.json").write_text('{"id":"id","title":"Test"}')
            self.assertEqual(distribution.audit(root)["candidates"][0]["status"],"awaiting-editorial-approval")
            p=root/"publish/approved";p.mkdir();(p/"id.json").write_text('{}')
            self.assertEqual(distribution.audit(root)["candidates"][0]["status"],"approved-awaiting-telegram")
            p=root/"publish/posted";p.mkdir();(p/"id.json").write_text('{}')
            row=distribution.audit(root)["candidates"][0]
            self.assertEqual(row["status"],"telegram-posted")
            self.assertEqual(row["x"],"paused")
            self.assertFalse((root/"publish/x-posted").exists())

    def test_rejected_candidate_never_looks_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            for name in ("candidates","rejected"):
                folder=root/"publish"/name;folder.mkdir(parents=True);(folder/"id.json").write_text('{"id":"id"}')
            self.assertEqual(distribution.audit(root)["candidates"][0]["status"],"rejected")

    def test_approval_card_has_manual_x_copy_and_retains_approval_buttons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);folder=root/"publish/candidates";folder.mkdir(parents=True)
            d={"id":"id","title":"Example launch","category":"NEWS","why_it_matters":"Details","article_url":"https://therwawire.com/news/example/","image_url":"https://therwawire.com/images/example.svg","caption":"Draft","sources":[{"name":"Issuer"}],"distribution":{"x":"Example launch\n\nhttps://therwawire.com/news/example/"}}
            (folder/"id.json").write_text(json.dumps(d));(root/"publish/channel-config.json").write_text('{"x_enabled":false}')
            with patch.object(editorial,"ROOT",root),patch.object(editorial,"CANDIDATES",folder),patch.dict("os.environ",{"TELEGRAM_REVIEW_CHAT_ID":"test-review-only"}),patch.object(editorial,"telegram") as send:
                editorial.request("publish/candidates/id.json")
            args=send.call_args.args
            self.assertIn("X API is paused",args[1]["text"])
            self.assertIn("utm_source=x",args[1]["text"])
            self.assertIn("approve:id",args[1]["reply_markup"])
            self.assertEqual(send.call_count,1)


if __name__=="__main__":unittest.main()
