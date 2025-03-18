import unittest
from tests.utils.api_client import get, head, post

class TestCategoriesDocumentedAPI(unittest.TestCase):
    """Tests that demonstrate documented (expected) behavior"""

    def setUp(self):
        self.test_category = {"title": "Test Category"}
        response = post("/categories", self.test_category,
                       headers={"Content-Type": "application/json"})
        self.category_id = response.json()["id"]

    def test_get_todos_invalid_category_documented(self):
        """According to documentation, invalid category should return 404"""
        print("NOTE: This test fails because API returns 200 for invalid category")
        response = get("/categories/999999/todos")
        self.assertEqual(response.status_code, 404,
                        "Should return 404 for invalid category")

    def test_get_projects_invalid_category_documented(self):
        """According to documentation, invalid category should return 404"""
        print("NOTE: This test fails because API returns 200 for invalid category")
        response = get("/categories/999999/projects")
        self.assertEqual(response.status_code, 404,
                        "Should return 404 for invalid category")

    def test_head_projects_invalid_category_documented(self):
        """According to documentation, HEAD for invalid category should return 404"""
        print("NOTE: This test fails because API returns 200 for invalid category")
        response = head("/categories/999999/projects")
        self.assertEqual(response.status_code, 404,
                        "Should return 404 for invalid category")
