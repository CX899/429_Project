import unittest
from tests.utils.api_client import get, post, delete

class TestTodoRelationships(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        # Create test todo
        self.test_todo = {"title": "Test Todo", "description": "Test Description"}
        todo_response = post("/todos", self.test_todo,
                            headers={"Content-Type": "application/json"})
        self.assertEqual(todo_response.status_code, 201)
        self.todo_id = todo_response.json()["id"]

        # Create test category
        self.test_category = {"title": "Test Category"}
        category_response = post("/categories", self.test_category,
                               headers={"Content-Type": "application/json"})
        self.assertEqual(category_response.status_code, 201)
        self.category_id = category_response.json()["id"]

        # Create test project
        self.test_project = {"title": "Test Project"}
        project_response = post("/projects", self.test_project,
                              headers={"Content-Type": "application/json"})
        self.assertEqual(project_response.status_code, 201)
        self.project_id = project_response.json()["id"]

    def tearDown(self):
        """Clean up test data"""
        delete(f"/todos/{self.todo_id}")
        delete(f"/categories/{self.category_id}")
        delete(f"/projects/{self.project_id}")

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
        """Test deleting a todo-tasksof relationship"""
        # First create a project
        project_data = {"title": "Test Project"}
        project_response = post("/projects", project_data,
                              headers={"Content-Type": "application/json"})
        self.assertEqual(project_response.status_code, 201)
        project_id = project_response.json()["id"]

        # Create the relationship
        relationship_data = {"id": project_id}
        post(f"/todos/{self.todo_id}/tasksof", relationship_data,
             headers={"Content-Type": "application/json"})

        # Now try to delete
        response = delete(f"/todos/{self.todo_id}/tasksof/{project_id}")
        self.assertEqual(response.status_code, 200)

    # Category Relationships
    def test_post_todo_category_invalid(self):
        response = post(f"/todos/{self.todo_id}/categories/1",
                       data={},  # Empty payload
                       headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 404)

    def test_delete_todo_category(self):
        """Test deleting a todo-category relationship"""
        # First create a category
        category_data = {"title": "Test Category"}
        category_response = post("/categories", category_data,
                            headers={"Content-Type": "application/json"})
        self.assertEqual(category_response.status_code, 201)
        category_id = category_response.json()["id"]

        # Create the relationship
        relationship_data = {"id": category_id}
        post(f"/todos/{self.todo_id}/categories", relationship_data,
            headers={"Content-Type": "application/json"})

        # Now try to delete
        response = delete(f"/todos/{self.todo_id}/categories/{category_id}")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
