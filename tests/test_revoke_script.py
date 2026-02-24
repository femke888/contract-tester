import subprocess
import tempfile
import unittest
from pathlib import Path


class TestRevokeScript(unittest.TestCase):
    def test_add_jti_entry(self):
        with tempfile.TemporaryDirectory() as td:
            revoked = Path(td) / "revoked.txt"
            cmd = [
                "python",
                "scripts/revoke_license.py",
                "--revoked-file",
                str(revoked),
                "--jti",
                "lic_123",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            content = revoked.read_text(encoding="utf-8")
            self.assertIn("lic_123", content)


if __name__ == "__main__":
    unittest.main()
