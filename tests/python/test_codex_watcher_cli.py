import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from codex_watcher import cli


class CodexWatcherCliTests(unittest.TestCase):
    def test_parse_inbox_file_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "stone.json"
            payload = {"canonical": "seed=a;prev=b;author=test", "digest": "abc"}
            path.write_text(json.dumps(payload), encoding="utf-8")

            canonical, digest = cli.parse_inbox_file(path)
            self.assertEqual(canonical, payload["canonical"])
            self.assertEqual(digest, payload["digest"])

    def test_parse_inbox_file_text(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "stone.txt"
            path.write_text("canonical=seed=a;prev=b;author=test\ndigest=def", encoding="utf-8")

            canonical, digest = cli.parse_inbox_file(path)
            self.assertEqual(canonical, "seed=a;prev=b;author=test")
            self.assertEqual(digest, "def")

    def test_validate_stone_success(self):
        tip = "tipdigest"
        canonical = f"seed=x;prev={tip};axis=y;author=test"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        valid, reason = cli.validate_stone(canonical, digest, tip)
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

    def test_validate_stone_prev_mismatch(self):
        canonical = "seed=x;prev=other;axis=y;author=test"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        valid, reason = cli.validate_stone(canonical, digest, "expected")
        self.assertFalse(valid)
        self.assertIn("prev mismatch", reason)

    def test_validate_stone_rejects_banned_term(self):
        tip = "tipdigest"
        canonical = f"seed=x;prev={tip};axis=secret-zone;author=test"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        valid, reason = cli.validate_stone(canonical, digest, tip)
        self.assertFalse(valid)
        self.assertIn("contains banned term", reason)


if __name__ == "__main__":
    unittest.main()
