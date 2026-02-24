import tempfile
import unittest
from pathlib import Path

from scripts.check_factory_readiness import _check_gitignore


class TestFactoryReadiness(unittest.TestCase):
    def test_gitignore_missing_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ".gitignore"
            path.write_text(".venv/\n", encoding="utf-8")
            issues = _check_gitignore(path)
            self.assertTrue(any("build/" in item for item in issues))


if __name__ == "__main__":
    unittest.main()
