import unittest
from tests.utils.api_client import get, post, delete

class TestTodoRelationships(unittest.TestCase):

    def setUp(self):
        """Create a test todo"""
        self.test_todo = {"title": "Sample Todo", "description": "Test Description"}
        todo_response = post("/todos", self.test_todo)
        self.assertEqual(todo_response.status_code, 201)
        self.todo_id = todo_response.json()["id"]

    def tearDown(self):
        """Cleanup test todo"""
        delete(f"/todos/{self.todo_id}")

    def print_results(self, endpoint, expected, actual):
        print(f"\n========== {endpoint} ==========")
        print(f"Expected: {expected}")
        print(f"Actual  : {actual}")
        if expected != actual:
            print("ISSUE: Unexpected result.")
        print("=================================\n")

    # TaskOf Relationships
    def test_get_todo_tasksof(self):
        response = get(f"/todos/{self.todo_id}/tasksof")
        self.print_results("GET /todos/:id/tasksof", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_post_todo_tasksof(self):
        related_task = {"title": "Related Task"}
        response = post(f"/todos/{self.todo_id}/tasksof", related_task)
        self.print_results("POST /todos/:id/tasksof", 201, response.status_code)
        self.assertEqual(response.status_code, 201)

    def test_delete_todo_tasksof(self):
        related_task = {"title": "Related Task"}
        post(f"/todos/{self.todo_id}/tasksof", related_task)  # Add task
        response = delete(f"/todos/{self.todo_id}/tasksof/1")
        self.print_results("DELETE /todos/:id/tasksof/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    # Category Relationships
    def test_post_todo_category_invalid(self):
        response = post(f"/todos/{self.todo_id}/categories/1")
        self.print_results("POST /todos/:id/categories/:id", 405, response.status_code)
        print("This should return 405 Method Not Allowed.")
        self.assertEqual(response.status_code, 405)

    def test_delete_todo_category(self):
        response = delete(f"/todos/{self.todo_id}/categories/1")
        self.print_results("DELETE /todos/:id/categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
