import unittest

from contract_tester.validate import validate_traffic_against_spec


class TestMaxErrors(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/1": {
                    "get": {
                        "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
                    }
                }
            },
        }
        self.traffic = [
            {"method": "GET", "path": "/missing/1", "status": 200, "response_json": {}},
            {"method": "GET", "path": "/missing/2", "status": 200, "response_json": {}},
            {"method": "GET", "path": "/missing/3", "status": 200, "response_json": {}},
        ]

    def test_stops_early(self):
        result = validate_traffic_against_spec(self.spec, self.traffic, max_errors=2)
        self.assertEqual(result["error_count"], 2)
        self.assertTrue(result["stopped_early"])


if __name__ == "__main__":
    unittest.main()
