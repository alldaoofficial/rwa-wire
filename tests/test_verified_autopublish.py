import copy
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import candidate_generator as generator
import source_review as review
import verified_autopublish as auto
from test_source_review import reviewed


class VerifiedAutoPublishTests(unittest.TestCase):
    def fixture(self):
        brief = reviewed(); brief["newsWatch"]["score"] = 6
        brief["pubDate"] = datetime.now(timezone.utc).date().isoformat()
        return review.seal(brief)

    def test_full_review_passes_without_scanner_self_approval(self):
        brief = self.fixture()
        self.assertFalse(brief["newsWatch"]["autoPublishEligible"])
        self.assertTrue(auto.eligible(brief, {"auto_publish_verified_rwa": True}))

    def test_hold_unreviewed_modified_stale_low_score_or_disabled(self):
        original = self.fixture()
        for mode in ["unreviewed", "changed", "low", "stale", "disabled", "crypto"]:
            brief = copy.deepcopy(original); policy = {"auto_publish_verified_rwa": True}
            if mode == "unreviewed": brief.pop("sourceReview")
            if mode == "changed": brief["body"] += " Unsupported change."
            if mode == "low": brief["newsWatch"]["score"] = 5
            if mode == "stale": brief["sourceReview"]["reviewedAt"] = "2000-01-01T00:00:00Z"
            if mode == "disabled": policy["auto_publish_verified_rwa"] = False
            if mode == "crypto": brief["cryptoWatch"] = brief.pop("newsWatch")
            self.assertFalse(auto.eligible(brief, policy), mode)

    def test_generated_copy_is_bound_and_rejection_or_receipt_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); brief = self.fixture()
            bp = root / "publish/inbox/story.json"; bp.parent.mkdir(parents=True)
            bp.write_text(json.dumps(brief))
            (root / "publish/editorial-policy.json").write_text('{"auto_publish_verified_rwa":true}')
            with patch.object(generator, "ROOT", root), patch.object(generator, "ARTICLES", root/"src/content/articles"), patch.object(generator, "IMAGES", root/"public/images/news"), patch.object(generator, "CANDIDATES", root/"publish/candidates"), patch.object(sys,"argv",["generator",str(bp)]):
                generator.main()
            cp = next((root/"publish/candidates").glob("*.json")); candidate = json.loads(cp.read_text())
            altered = copy.deepcopy(candidate); altered["caption"] += " Unreviewed advertisement."
            cp.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,"differs"): auto.approve(str(bp.relative_to(root)),str(cp.relative_to(root)),root)
            self.assertFalse((root/"publish/approved").exists())
            cp.write_text(json.dumps(candidate))
            rejected=root/"publish/rejected"/cp.name; rejected.parent.mkdir(); rejected.write_text('{}')
            with self.assertRaisesRegex(ValueError,"Rejected"): auto.approve(str(bp.relative_to(root)),str(cp.relative_to(root)),root)
            rejected.unlink()
            result=auto.approve(str(bp.relative_to(root)),str(cp.relative_to(root)),root)
            self.assertTrue((root/result).exists())
            self.assertEqual(json.loads((root/result).read_text())["automaticApproval"]["contentSha256"],brief["sourceReview"]["contentSha256"])
            posted=root/"publish/posted"/cp.name; posted.parent.mkdir(); posted.write_text('{"status":"published"}')
            self.assertEqual(auto.approve(str(bp.relative_to(root)),str(cp.relative_to(root)),root),"")


if __name__ == "__main__": unittest.main()
