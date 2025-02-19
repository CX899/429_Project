import unittest
from tests.utils.api_client import get, post, put, delete

class TestCategoriesAPI(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test"""
        self.test_category = {"title": "Test Category", "description": "For unit testing"}
        response = post("/categories", self.test_category)
        self.assertEqual(response.status_code, 201)
        self.category_id = response.json().get("id")

    def tearDown(self):
        """Cleanup: Delete the test category after each test"""
        delete(f"/categories/{self.category_id}")

    def print_results(self, endpoint, expected, actual):
        print(f"\n========== {endpoint} ==========")
        print(f"Expected: {expected}")
        print(f"Actual  : {actual}")
        print("=================================\n")

    def test_get_all_categories(self):
        response = get("/categories")
        self.print_results("GET /categories", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_category_by_id(self):
        response = get(f"/categories/{self.category_id}")
        self.print_results("GET /categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_post_category(self):
        new_category = {"title": "New Category", "description": "New Desc"}
        response = post("/categories", new_category)
        self.print_results("POST /categories", 201, response.status_code)
        self.assertEqual(response.status_code, 201)

    def test_put_category(self):
        update_data = {"title": "Updated Title", "description": "Updated Desc"}
        response = put(f"/categories/{self.category_id}", update_data)
        self.print_results("PUT /categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_delete_category(self):
        response = delete(f"/categories/{self.category_id}")
        self.print_results("DELETE /categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()