import os
import tempfile
import unittest

from contract_tester.traffic import load_traffic


class TestTrafficCurl(unittest.TestCase):
    def _write_file(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_curl_log_parsing(self):
        content = """curl -s -X POST https://api.example.com/users -H "Accept: application/json"
{"id": 1, "name": "Ada"}
HTTPSTATUS:201
"""
        path = self._write_file(content, ".log")
        try:
            items = load_traffic(path)
        finally:
            os.remove(path)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["method"], "POST")
        self.assertEqual(items[0]["path"], "/users")
        self.assertEqual(items[0]["status"], 201)
        self.assertEqual(items[0]["response_json"]["name"], "Ada")


if __name__ == "__main__":
    unittest.main()
