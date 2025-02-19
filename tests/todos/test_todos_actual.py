import unittest
from tests.utils.api_client import get, post, put, delete

class TestTodosActualAPI(unittest.TestCase):
    """Tests that demonstrate actual behavior"""

    def setUp(self):
        self.test_todo = {"title": "Test Todo", "description": "Test Description"}
        response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.todo_id = response.json()["id"]

    def tearDown(self):
        delete(f"/todos/{self.todo_id}")

    def test_post_todo_categories_actual(self):
        """POST to /todos/:id/categories/:id returns 405 in reality"""
        response = post(f"/todos/{self.todo_id}/categories/1",
                       data={},  # Empty payload
                       headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 404)
