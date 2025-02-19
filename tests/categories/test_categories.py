import unittest
from tests.utils.api_client import get, post, put, delete, head

class TestCategoriesAPI(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test"""
        self.test_category = {"title": "Test Category", "description": "For unit testing"}
        response = post("/categories", self.test_category)
        self.assertEqual(response.status_code, 200)
        self.category_id = response.json().get("id")

    def tearDown(self):
        """Cleanup: Delete the test category after each test"""
        delete(f"/categories/{self.category_id}")

    def test_get_all_categories(self):
        response = get("/categories")
        self.assertEqual(response.status_code, 200)

    def test_get_category_by_id(self):
        response = get(f"/categories/{self.category_id}")
        self.assertEqual(response.status_code, 200)

    def test_post_category(self):
        new_category = {"title": "New Category", "description": "New Desc"}
        response = post("/categories", new_category)
        self.assertEqual(response.status_code, 200)

    def test_put_category(self):
        update_data = {"title": "Updated Title", "description": "Updated Desc"}
        response = put(f"/categories/{self.category_id}", update_data)
        self.assertEqual(response.status_code, 200)

    def test_delete_category(self):
        response = delete(f"/categories/{self.category_id}")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
