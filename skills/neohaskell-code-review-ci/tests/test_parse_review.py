"""Consumer-maintained examples for the bundled parser, not a collection release gate."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("parse_review", ROOT / "scripts/parse_review.py")
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)


class ParseReviewTests(unittest.TestCase):
    def test_clean_prose_containing_blocker_is_clean(self):
        self.assertEqual(parser.main([str(ROOT / "fixtures/clean.json"), "--reviewer-exit-code", "0"]), 0)

    def test_structured_blocker_fails(self):
        self.assertEqual(parser.main([str(ROOT / "fixtures/blocker.json"), "--reviewer-exit-code", "0"]), 1)

    def test_malformed_output_is_not_approval(self):
        self.assertEqual(parser.main([str(ROOT / "fixtures/malformed.txt"), "--reviewer-exit-code", "0"]), 2)

    def test_failed_reviewer_cannot_approve_with_stale_output(self):
        self.assertEqual(parser.main([str(ROOT / "fixtures/clean.json"), "--reviewer-exit-code", "7"]), 3)

    def test_duplicate_keys_are_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review.json"
            output.write_text('{"summary":"ok","findings":[],"findings":[]}')
            self.assertEqual(parser.main([str(output), "--reviewer-exit-code", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
