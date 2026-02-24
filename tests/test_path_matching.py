import unittest

from contract_tester.openapi import get_operation


class TestPathMatching(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/me": {"get": {"responses": {"200": {}}}},
                "/users/{id}/posts/latest": {"get": {"responses": {"200": {}}}},
                "/users/{id}": {"get": {"responses": {"200": {}}}},
                "/users/{id}/posts/{postId}": {"get": {"responses": {"200": {}}}},
            },
        }

    def test_exact_match_wins(self):
        op = get_operation(self.spec, "/users/me", "GET")
        self.assertIsNotNone(op)

    def test_template_match(self):
        op = get_operation(self.spec, "/users/123", "GET")
        self.assertIsNotNone(op)

    def test_best_specificity(self):
        op = get_operation(self.spec, "/users/123/posts/999", "GET")
        self.assertIsNotNone(op)

    def test_static_segment_wins(self):
        op = get_operation(self.spec, "/users/123/posts/latest", "GET")
        self.assertIsNotNone(op)

    def test_no_match(self):
        op = get_operation(self.spec, "/projects/1", "GET")
        self.assertIsNone(op)

    def test_trailing_slash_match(self):
        op = get_operation(self.spec, "/users/123/", "GET")
        self.assertIsNotNone(op)

    def test_query_string_ignored(self):
        op = get_operation(self.spec, "/users/123?x=1", "GET")
        self.assertIsNotNone(op)


if __name__ == "__main__":
    unittest.main()
