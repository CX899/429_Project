import unittest
from tests.utils.api_client import get, head, post

class TestCategoriesActualAPI(unittest.TestCase):
    """Tests that demonstrate actual behavior"""

    def setUp(self):
        self.test_category = {"title": "Test Category"}
        response = post("/categories", self.test_category,
                       headers={"Content-Type": "application/json"})
        self.category_id = response.json()["id"]

    def test_get_todos_invalid_category_actual(self):
        """Document actual behavior: returns 200 for invalid category"""
        response = get("/categories/999999/todos")
        self.assertEqual(response.status_code, 200,
                        "API returns 200 even for invalid category (potential bug)")

    def test_get_projects_invalid_category_actual(self):
        """Document actual behavior: returns 200 for invalid category"""
        response = get("/categories/999999/projects")
        self.assertEqual(response.status_code, 200,
                        "API returns 200 even for invalid category (potential bug)")

    def test_head_projects_invalid_category_actual(self):
        """Document actual behavior: returns 200 for invalid category"""
        response = head("/categories/999999/projects")
        self.assertEqual(response.status_code, 200,
                        "API returns 200 even for invalid category (potential bug)")
