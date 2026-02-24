import base64
import json
import os
import tempfile
import unittest

from contract_tester.traffic import load_traffic


class TestTrafficHar(unittest.TestCase):
    def _write_file(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_base64_json_response(self):
        payload = {"ok": True}
        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")

        har = {
            "log": {
                "entries": [
                    {
                        "request": {"method": "GET", "url": "https://example.com/api"},
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": encoded,
                                "encoding": "base64",
                            },
                        },
                    }
                ]
            }
        }

        har_path = self._write_file(json.dumps(har), ".har")
        try:
            items = load_traffic(har_path)
        finally:
            os.remove(har_path)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["response_json"], payload)


if __name__ == "__main__":
    unittest.main()
