import unittest
from tests.utils.api_client import get, post, put, delete, head

class TestCategoryRelationships(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test"""
        self.test_category = {"title": "Work", "description": "Test"}
        category_response = post("/categories", self.test_category, headers={"Content-Type": "application/json"})
        self.assertEqual(category_response.status_code, 201)
        self.category_id = category_response.json()["id"]

        self.test_project = {"title": "Project1", "description": "Test Project"}
        project_response = post("/projects", self.test_project, headers={"Content-Type": "application/json"})
        self.assertEqual(project_response.status_code, 201)
        self.project_id = project_response.json()["id"]

        self.test_todo = {"title": "todo1", "description": "Test todo"}
        todo_response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(todo_response.status_code, 201)
        self.todo_id = todo_response.json()["id"]

    def tearDown(self):
        """Cleanup test data after each test"""
        delete(f"/categories/{self.category_id}")
        delete(f"/projects/{self.project_id}")
        delete(f"/todos/{self.todo_id}")

    def print_results(self, endpoint, expected, actual):
        print(f"\n========== {endpoint} ==========")
        print(f"Expected: {expected}")
        print(f"Actual  : {actual}")
        if expected != actual:
            print("ISSUE: Unexpected result!")
        print("=================================\n")

    # HEAD Requests for Categories
    def test_head_all_categories(self):
        response = head("/categories")
        self.print_results("HEAD /categories", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_head_category_by_id(self):
        response = head(f"/categories/{self.category_id}")
        self.print_results("HEAD /categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_head_category_invalid_id(self):
        response = head("/categories/999999")
        self.print_results("HEAD /categories/:id (invalid ID)", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    # GET Requests for Todos Relationship
    def test_get_category_todos_empty(self):
        response = get(f"/categories/{self.category_id}/todos")
        self.print_results("GET /categories/:id/todos (empty)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'todos': []})

    # POST Requests for Todos Relationship
    def test_post_todo_to_category(self):
        todo_data = {"title": "New Todo", "description": "Todo Test"}
        response = post(f"/categories/{self.category_id}/todos", todo_data, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories/:id/todos", 201, response.status_code)
        self.assertEqual(response.status_code, 201)

    def test_post_duplicate_todo_to_category(self):
        """Note: The API allows duplicate todos in categories (potential issue)"""
        todo_data = {"title": "New Todo", "description": "Todo Test"}
        # First addition
        post(f"/categories/{self.category_id}/todos", todo_data,
             headers={"Content-Type": "application/json"})
        # Second addition of same todo
        response = post(f"/categories/{self.category_id}/todos", todo_data,
                       headers={"Content-Type": "application/json"})
        # Document that this is potentially unexpected behavior
        self.assertEqual(response.status_code, 201,
                        "NOTE: API allows duplicate todos in categories")

    # DELETE Requests for Todos Relationship
    def test_delete_invalid_category_todo_relationship(self):
        response = delete("/categories/999999/todos/999999")
        self.print_results("DELETE /categories/:id/todos/:id (invalid relationship)", 404, response.status_code)
        if response.status_code == 200:
            print("ISSUE: Deleting a non-existent relationship returned 200!")
        self.assertEqual(response.status_code, 404)

    # GET Requests for Project Relationship
    def test_get_projects_for_category(self):
        response = get(f"/categories/{self.category_id}/projects")
        self.print_results("GET /categories/:id/projects", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_projects_invalid_category(self):
        """Test getting projects for invalid category (actual behavior)"""
        response = get("/categories/999999/projects")
        # Document actual behavior: returns 200 even for invalid category
        self.assertEqual(response.status_code, 200,
                        "NOTE: API returns 200 for invalid category (documented as 404)")

    def test_get_todos_invalid_category(self):
        """Test getting todos for invalid category (actual behavior)"""
        response = get("/categories/999999/todos")
        # Document actual behavior: returns 200 even for invalid category
        self.assertEqual(response.status_code, 200,
                        "NOTE: API returns 200 for invalid category (documented as 404)")

    def test_head_projects_invalid_category(self):
        """Test HEAD request for invalid category (actual behavior)"""
        response = head("/categories/999999/projects")
        # Document actual behavior: returns 200 even for invalid category
        self.assertEqual(response.status_code, 200,
                        "NOTE: API returns 200 for invalid category (documented as 404)")

    # POST Requests for Project Relationship
    def test_post_project_to_category(self):
        response = post(f"/categories/{self.category_id}/projects", {"id": self.project_id}, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories/:id/projects", 201, response.status_code)
        self.assertEqual(response.status_code, 201)

    # DELETE Requests for Project Relationship
    def test_remove_project_from_category(self):
        post(f"/categories/{self.category_id}/projects", {"id": self.project_id}, headers={"Content-Type": "application/json"})
        response = delete(f"/categories/{self.category_id}/projects/{self.project_id}")
        self.print_results("DELETE /categories/:id/projects/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_delete_invalid_category_project_relationship(self):
        response = delete("/categories/999999/projects/999999")
        self.print_results("DELETE /categories/:id/projects/:id (invalid relationship)", 404, response.status_code)
        if response.status_code == 200:
            print("ISSUE: Deleting a non-existent relationship returned 200!")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
