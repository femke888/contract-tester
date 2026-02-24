import json
import unittest
from io import StringIO
from unittest.mock import patch

from contract_tester import cli


class TestCli(unittest.TestCase):
    def test_license_status_without_subcommand(self):
        fake_out = StringIO()
        with patch("sys.stdout", fake_out):
            with patch("contract_tester.cli.get_license_status", return_value={"valid": False, "code": "missing_key"}):
                rc = cli.main(["--license-status", "--license-json"])
        self.assertEqual(rc, 1)
        payload = json.loads(fake_out.getvalue())
        self.assertEqual(payload["code"], "missing_key")

    def test_missing_command_returns_2(self):
        fake_err = StringIO()
        with patch("sys.stderr", fake_err):
            rc = cli.main([])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
