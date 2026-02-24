import tempfile
import unittest
from pathlib import Path

from scripts.write_checksums import write_checksums


class TestWriteChecksums(unittest.TestCase):
    def test_write_checksums_ignores_existing_sums_file(self):
        with tempfile.TemporaryDirectory() as td:
            dist = Path(td) / "dist"
            dist.mkdir()
            (dist / "a.bin").write_bytes(b"abc")
            (dist / "b.bin").write_bytes(b"xyz")
            (dist / "SHA256SUMS.txt").write_text("old\n", encoding="ascii")

            out = dist / "SHA256SUMS.txt"
            lines = write_checksums(dist, out)
            text = out.read_text(encoding="ascii")

            self.assertEqual(len(lines), 2)
            self.assertIn("a.bin", text)
            self.assertIn("b.bin", text)
            self.assertNotIn("old", text)


if __name__ == "__main__":
    unittest.main()
