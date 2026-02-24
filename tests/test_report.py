import os
import tempfile
import unittest

from contract_tester.report import build_html_report


class TestReport(unittest.TestCase):
    def test_report_contains_error_count(self):
        result = {
            "total_checks": 2,
            "error_count": 1,
            "errors": ["bad"],
            "errors_grouped": {"GET /x 200": ["bad"]},
            "stopped_early": False,
        }
        html = build_html_report(result)
        self.assertIn("Errors:", html)
        self.assertIn("bad", html)
        self.assertIn("Error groups", html)

    def test_report_write(self):
        result = {"total_checks": 1, "error_count": 0, "errors": [], "stopped_early": False}
        html = build_html_report(result)
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.assertIn("Contract Tester Report", data)
        finally:
            os.remove(path)

    def test_report_demo_banner(self):
        result = {
            "total_checks": 1,
            "error_count": 0,
            "errors": [],
            "stopped_early": False,
            "license_status": {"valid": False},
        }
        html = build_html_report(result)
        self.assertIn("Demo mode", html)


if __name__ == "__main__":
    unittest.main()
