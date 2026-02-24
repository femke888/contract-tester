import json
import os
import tempfile
import unittest
from unittest.mock import patch

from contract_tester.openapi import load_spec
from contract_tester.traffic import load_traffic
from contract_tester.validate import validate_traffic_against_spec


class TestValidateE2E(unittest.TestCase):
    def _write_file(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_validate_success_and_failure(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/123": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"id": {"type": "number"}},
                                            "required": ["id"],
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "GET", "path": "/users/123?debug=1", "status": 200, "response_json": {"id": 1}},
            {"method": "GET", "path": "/users/123/", "status": 200, "response_json": {"name": "Ada"}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 1)

    def test_ignore_unknown(self):
        spec = {"openapi": "3.0.0", "paths": {}}
        traffic = [
            {"method": "GET", "path": "/users/1", "status": 200, "response_json": {}},
            {"method": "GET", "path": "/users/2", "status": 200, "response_json": {}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic, ignore_unknown=True)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 0)

    def test_ref_resolution(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"id": {"type": "number"}},
                        "required": ["id"],
                    }
                }
            },
            "paths": {
                "/users/1": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "GET", "path": "/users/1", "status": 200, "response_json": {"id": 1}},
            {"method": "GET", "path": "/users/1", "status": 200, "response_json": {"name": "Ada"}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 1)

    def test_ref_recursion(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "User": {"$ref": "#/components/schemas/BaseUser"},
                    "BaseUser": {
                        "type": "object",
                        "properties": {"id": {"type": "number"}},
                        "required": ["id"],
                    },
                }
            },
            "paths": {
                "/users/1": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "GET", "path": "/users/1", "status": 200, "response_json": {"id": 1}},
            {"method": "GET", "path": "/users/1", "status": 200, "response_json": {"name": "Ada"}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 1)

    def test_status_class_response(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/123": {
                    "get": {
                        "responses": {
                            "2XX": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"ok": {"type": "boolean"}},
                                            "required": ["ok"],
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "GET", "path": "/users/123", "status": 200, "response_json": {"ok": True}},
            {"method": "GET", "path": "/users/123", "status": 204, "response_json": {"ok": False}},
            {"method": "GET", "path": "/users/123", "status": 299, "response_json": {"missing": 1}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 3)
        self.assertEqual(result["error_count"], 1)

    def test_plus_json_content_type(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/events": {
                    "post": {
                        "responses": {
                            "201": {
                                "content": {
                                    "application/vnd.api+json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"id": {"type": "string"}},
                                            "required": ["id"],
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "POST", "path": "/events", "status": 201, "response_json": {"id": "evt_1"}},
            {"method": "POST", "path": "/events", "status": 201, "response_json": {"name": "bad"}},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 1)

    def test_no_content_204(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/cleanup": {
                    "delete": {
                        "responses": {
                            "204": {"description": "No Content"},
                        }
                    }
                }
            },
        }
        traffic = [
            {"method": "DELETE", "path": "/cleanup", "status": 204, "response_json": None},
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 1)
        self.assertEqual(result["error_count"], 0)

    def test_request_parameters_and_body(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/{id}": {
                    "parameters": [
                        {"name": "x-trace-id", "in": "header", "required": True, "schema": {"type": "string"}}
                    ],
                    "post": {
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
                            {"name": "active", "in": "query", "required": True, "schema": {"type": "boolean"}},
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                        "required": ["name"],
                                    }
                                }
                            },
                        },
                        "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                    },
                }
            },
        }
        traffic = [
            {
                "method": "POST",
                "path": "/users/123",
                "status": 200,
                "response_json": {},
                "query": {"active": "true"},
                "headers": {"X-Trace-Id": "abc"},
                "request_json": {"name": "Ada"},
                "request_content_type": "application/json",
            },
            {
                "method": "POST",
                "path": "/users/abc",
                "status": 200,
                "response_json": {},
                "query": {},
                "headers": {},
                "request_json": {"bad": True},
                "request_content_type": "application/json",
            },
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertGreaterEqual(result["error_count"], 3)

    def test_demo_mode_limits(self):
        spec = {"openapi": "3.0.0", "paths": {f"/p{i}": {"get": {"responses": {"200": {}}}} for i in range(40)}}
        traffic = [
            {"method": "GET", "path": "/p1", "status": 200, "response_json": {}}
            for _ in range(60)
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            from contract_tester.cli import build_parser

            with patch("contract_tester.license.get_license_status", return_value={"valid": False}):
                parser = build_parser()
                args = parser.parse_args(
                    ["validate", "--spec", spec_path, "--traffic", traffic_path]
                )
                exit_code = args.func(args)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(exit_code, 2)

    def test_request_body_sniff_without_content_type(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/items": {
                    "post": {
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "number"}},
                                        "required": ["id"],
                                    }
                                }
                            },
                        },
                        "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                    }
                }
            },
        }
        traffic = [
            {
                "method": "POST",
                "path": "/items",
                "status": 200,
                "response_json": {},
                "request_text": "{\"id\": 1}",
                "request_content_type": None,
            },
            {
                "method": "POST",
                "path": "/items",
                "status": 200,
                "response_json": {},
                "request_text": "{\"bad\": true}",
                "request_content_type": None,
            },
        ]

        spec_path = self._write_file(json.dumps(spec), ".json")
        traffic_path = self._write_file(json.dumps(traffic), ".json")

        try:
            loaded_spec = load_spec(spec_path)
            loaded_traffic = load_traffic(traffic_path)
            result = validate_traffic_against_spec(loaded_spec, loaded_traffic)
        finally:
            os.remove(spec_path)
            os.remove(traffic_path)

        self.assertEqual(result["total_checks"], 2)
        self.assertEqual(result["error_count"], 1)


if __name__ == "__main__":
    unittest.main()
