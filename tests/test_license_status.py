import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contract_tester.license import get_license_status


class TestLicenseStatus(unittest.TestCase):
    def test_missing_key_status(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            missing_a = base / "a.key"
            missing_b = base / "b.key"
            with patch("contract_tester.license._license_locations", return_value=(missing_a, missing_b)):
                with patch.dict(
                    os.environ,
                    {
                        "CONTRACT_TESTER_LICENSE": "",
                        "CONTRACT_TESTER_LICENSE_FILE": "",
                    },
                    clear=False,
                ):
                    status = get_license_status()
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "missing_key")
        self.assertIsNone(status["source"])


if __name__ == "__main__":
    unittest.main()
