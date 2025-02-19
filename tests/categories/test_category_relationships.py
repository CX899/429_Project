import unittest
from tests.utils.api_client import get, post, delete

class TestCategoryRelationships(unittest.TestCase):

    def setUp(self):
        """Create a test category"""
        self.test_category = {"title": "Work", "description": "Test"}
        category_response = post("/categories", self.test_category)
        self.assertEqual(category_response.status_code, 200)
        self.category_id = category_response.json()["id"]

        """Create a test project"""
        self.test_project = {"title": "Project1", "description": "Test Project"}
        project_response = post("/projects", self.test_project)
        self.assertEqual(project_response.status_code, 200)
        self.project_id = project_response.json()["id"]

    def tearDown(self):
        """Cleanup category & project"""
        delete(f"/categories/{self.category_id}")
        delete(f"/projects/{self.project_id}")

    def test_add_project_to_category(self):
        """Test POST /categories/:id/projects"""
        response = post(f"/categories/{self.category_id}/projects", {"id": self.project_id})
        self.assertEqual(response.status_code, 201)

    def test_get_projects_for_category(self):
        """Test GET /categories/:id/projects"""
        response = get(f"/categories/{self.category_id}/projects")
        self.assertEqual(response.status_code, 200)

    def test_remove_project_from_category(self):
        """Test DELETE /categories/:id/projects/:id"""
        post(f"/categories/{self.category_id}/projects", {"id": self.project_id})
        response = delete(f"/categories/{self.category_id}/projects/{self.project_id}")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
