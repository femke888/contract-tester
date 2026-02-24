import subprocess
import tempfile
import unittest
from pathlib import Path


class TestGenerateLicenseKeysScript(unittest.TestCase):
    def test_generate_keys(self):
        with tempfile.TemporaryDirectory() as td:
            private_out = Path(td) / "private.pem"
            public_out = Path(td) / "public.pem"
            cmd = [
                "python",
                "scripts/generate_license_keys.py",
                "--private-out",
                str(private_out),
                "--public-out",
                str(public_out),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(private_out.exists())
            self.assertTrue(public_out.exists())
            self.assertIn("BEGIN PRIVATE KEY", private_out.read_text(encoding="utf-8"))
            self.assertIn("BEGIN PUBLIC KEY", public_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
