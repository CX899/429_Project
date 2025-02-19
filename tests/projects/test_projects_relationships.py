import unittest
from tests.utils.api_client import get, post, delete


class TestProjectRelationships(unittest.TestCase):

    def setUp(self):
        """Create a test project and test todo before each test"""
        self.test_project = {
            "title": "Test Project",
            "description": "For relationship testing",
        }
        project_response = post("/projects", self.test_project)
        self.assertEqual(project_response.status_code, 201)
        self.project_id = project_response.json()["id"]

        self.test_todo = {
            "title": "Test Todo",
            "doneStatus": False,
            "description": "A task",
        }
        todo_response = post("/todos", self.test_todo)
        self.assertEqual(todo_response.status_code, 201)
        self.todo_id = todo_response.json()["id"]

    def tearDown(self):
        """Cleanup test data after each test"""
        delete(f"/projects/{self.project_id}")
        delete(f"/todos/{self.todo_id}")

    def test_add_todo_to_project(self):
        """Test linking a todo to a project"""
        response = post(f"/projects/{self.project_id}/tasks", {"id": self.todo_id})
        self.assertEqual(response.status_code, 201)

    def test_get_todos_for_project(self):
        """Test retrieving todos linked to a project"""
        post(f"/projects/{self.project_id}/tasks", {"id": self.todo_id})
        response = get(f"/projects/{self.project_id}/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(todo["id"] == self.todo_id for todo in response.json()))

    def test_remove_todo_from_project(self):
        """Test removing a todo from a project"""
        post(f"/projects/{self.project_id}/tasks", {"id": self.todo_id})
        response = delete(f"/projects/{self.project_id}/tasks/{self.todo_id}")
        self.assertEqual(response.status_code, 200)

    def test_add_non_existent_todo_to_project(self):
        """Test attempting to add a non-existent todo to a project"""
        response = post(f"/projects/{self.project_id}/tasks", {"id": "999999"})
        self.assertEqual(response.status_code, 404)

    def test_remove_non_existent_todo_from_project(self):
        """Test attempting to remove a non-existent todo from a project"""
        response = delete(f"/projects/{self.project_id}/tasks/999999")
        self.assertEqual(response.status_code, 404)

    def test_malformed_json_payload(self):
        """Test sending malformed JSON when adding a todo to a project"""
        response = post(f"/projects/{self.project_id}/tasks", "{id:}")
        self.assertEqual(response.status_code, 400)

    def test_malformed_xml_payload(self):
        """Test sending malformed XML payload"""
        headers = {"Content-Type": "application/xml"}
        payload = "<task><id></id></task>"
        response = post(f"/projects/{self.project_id}/tasks", payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_delete_already_deleted_relationship(self):
        """Test deleting a todo from a project twice"""
        post(f"/projects/{self.project_id}/tasks", {"id": self.todo_id})
        delete(f"/projects/{self.project_id}/tasks/{self.todo_id}")
        response = delete(f"/projects/{self.project_id}/tasks/{self.todo_id}")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
