import subprocess
import tempfile
import unittest
from pathlib import Path


class TestRevokeAndNoteScript(unittest.TestCase):
    def test_add_entry_with_reason_comment(self):
        with tempfile.TemporaryDirectory() as td:
            revoked = Path(td) / "revoked.txt"
            cmd = [
                "python",
                "scripts/revoke_and_note.py",
                "--revoked-file",
                str(revoked),
                "--jti",
                "lic_456",
                "--reason",
                "refund",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            content = revoked.read_text(encoding="utf-8")
            self.assertIn("reason=refund", content)
            self.assertIn("lic_456", content)


if __name__ == "__main__":
    unittest.main()
