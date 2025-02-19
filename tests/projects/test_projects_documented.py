import unittest
from tests.utils.api_client import get, post, put, delete

class TestProjectsDocumentedAPI(unittest.TestCase):
    """Tests that demonstrate actual behavior"""

    def setUp(self):
        self.test_todo = {"title": "Test Projects", "description": "Test Description"}
        response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.todo_id = response.json()["id"]

    def tearDown(self):
        delete(f"/todos/{self.todo_id}")

    def test_post_empty_body_documented(self):
        """This test demonstrates the documented behavior (should reject empty body)"""
        print("NOTE: This test fails because the API accepts empty bodies")
        response = post("/projects", {}, headers={"Content-Type": "application/json"})
        # Keep this to document the expected behavior
        self.assertEqual(response.status_code, 400,
                        "API should reject empty body according to documentation")
