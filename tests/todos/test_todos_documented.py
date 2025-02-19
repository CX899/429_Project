import unittest
from tests.utils.api_client import get, post, put, delete

class TestTodosDocumentedAPI(unittest.TestCase):
    """Tests that demonstrate documented behavior (even if they fail)"""

    def setUp(self):
        self.test_todo = {"title": "Test Todo", "description": "Test Description"}
        response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.todo_id = response.json()["id"]

    def tearDown(self):
        delete(f"/todos/{self.todo_id}")

    def test_post_todo_categories_documented(self):
        """Should be able to POST to /todos/:id/categories/:id according to docs"""
        response = post(f"/todos/{self.todo_id}/categories/1",
                       data={},  # Empty payload
                       headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 200)
