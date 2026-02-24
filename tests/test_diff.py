import unittest

from contract_tester.diff import diff_specs


class TestDiff(unittest.TestCase):
    def test_removed_operation_and_response(self):
        old_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {"get": {"responses": {"200": {}}}},
            },
        }
        new_spec = {
            "openapi": "3.0.0",
            "paths": {},
        }

        result = diff_specs(old_spec, new_spec)
        self.assertTrue(any("Removed operation GET /users" in x for x in result["breaking_changes"]))

    def test_schema_change_detected(self):
        old_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {"type": "string"}}}
                            }
                        }
                    }
                }
            },
        }
        new_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {"type": "number"}}}
                            }
                        }
                    }
                }
            },
        }

        result = diff_specs(old_spec, new_spec)
        self.assertTrue(any("Schema changed GET /users 200" in x for x in result["breaking_changes"]))


if __name__ == "__main__":
    unittest.main()
