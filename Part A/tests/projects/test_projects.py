import unittest
from tests.utils.api_client import get, post, put, delete


class TestProjectsAPI(unittest.TestCase):
    def setUp(self):
        """Ensure a clean state before each test"""
        self.test_project = {
            "title": "Test Project",
            "description": "For unit testing"
        }
        response = post("/projects", self.test_project,
                       headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.project_id = response.json().get("id")  # Make sure this line exists

        self.test_todo = {"title": "Test Todo", "description": "Test todo"}
        todo_response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(todo_response.status_code, 201)
        self.todo_id = todo_response.json()["id"]

    def tearDown(self):
        """Restore system to initial state"""
        # Delete test data
        delete(f"/todos/{self.todo_id}")

    def print_results(self, endpoint, expected, actual):
        print(f"\n========== {endpoint} ==========")
        print(f"Expected: {expected}")
        print(f"Actual  : {actual}")
        print("=================================\n")

    def test_get_all_projects(self):
        response = get("/projects")
        self.print_results("GET /projects", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_project_by_id(self):
        response = get(f"/projects/{self.project_id}")
        self.print_results("GET /projects/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_non_existent_project(self):
        response = get("/projects/999999")
        self.print_results("GET /projects/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_post_project(self):
        new_project = {"title": "New Project", "description": "New Desc"}
        response = post("/projects", new_project)
        self.print_results("POST /projects", 201, response.status_code)
        self.assertEqual(response.status_code, 201)

    def test_post_empty_body(self):
        """Test posting empty body (actual behavior)"""
        response = post("/projects", {}, headers={"Content-Type": "application/json"})
        # Document actual behavior
        self.assertEqual(response.status_code, 201,
                        "NOTE: API accepts empty body for POST requests")

    def test_put_empty_body(self):
        """Test putting empty body (actual behavior)"""
        response = put(f"/projects/{self.project_id}", {},
                      headers={"Content-Type": "application/json"})
        # Document actual behavior
        self.assertEqual(response.status_code, 200,
                        "NOTE: API accepts empty body for PUT requests")

    def test_post_invalid_field_type(self):
        new_project = {"title": "Invalid Project", "completed": "not a boolean"}
        response = post("/projects", new_project)
        self.print_results(
            "POST /projects (invalid field type)", 400, response.status_code
        )
        self.assertEqual(response.status_code, 400)

    def test_put_project(self):
        update_data = {"title": "Updated Title", "description": "Updated Desc"}
        response = put(f"/projects/{self.project_id}", update_data)
        self.print_results("PUT /projects/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_put_non_existent_project(self):
        update_data = {"title": "Ghost Project"}
        response = put("/projects/999999", update_data)
        self.print_results("PUT /projects/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_delete_project(self):
        response = delete(f"/projects/{self.project_id}")
        self.print_results("DELETE /projects/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_delete_already_deleted_project(self):
        delete(f"/projects/{self.project_id}")  # First delete
        response = delete(f"/projects/{self.project_id}")  # Try again
        self.print_results(
            "DELETE /projects/:id (already deleted)", 404, response.status_code
        )
        self.assertEqual(response.status_code, 404)

    def test_malformed_json(self):
        malformed_data = (
            '{"title": "Broken JSON", "description": "Oops"'  # Missing closing bracket
        )
        response = post("/projects", malformed_data)
        self.print_results("POST /projects (malformed JSON)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_malformed_xml(self):
        malformed_xml = "<project><title>Broken XML<title></project>"  # Malformed XML
        headers = {"Content-Type": "application/xml"}
        response = post("/projects", malformed_xml, headers=headers)
        self.print_results("POST /projects (malformed XML)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
