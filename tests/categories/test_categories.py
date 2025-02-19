import unittest
from tests.utils.api_client import get, post, put, delete

class TestCategoriesAPI(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test"""
        # Verify system is running
        response = get("/")
        self.assertEqual(response.status_code, 200)

        # Save initial state
        self.initial_state = get("/todos").json()

        self.test_category = {"title": "WorkTest", "description": "TestTEST"}
        category_response = post("/categories", self.test_category, headers={"Content-Type": "application/json"})
        self.assertEqual(category_response.status_code, 201)
        self.category_id = category_response.json()["id"]

        # Create test data
        self.test_todo = {"title": "Test Todo", "description": "Test Description"}
        response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.todo_id = response.json()["id"]

    def tearDown(self):
        """Restore system to initial state"""
        # Delete test data
        delete(f"/categories/{self.category_id}")
        delete(f"/todos/{self.todo_id}")

        # Verify state is restored
        current_state = get("/todos").json()
        self.assertEqual(
            len(current_state),
            len(self.initial_state),
            "System state not properly restored"
        )

    def print_results(self, endpoint, expected, actual):
        print(f"\n========== {endpoint} ==========")
        print(f"Expected: {expected}")
        print(f"Actual  : {actual}")
        if expected != actual:
            print("ISSUE: Unexpected result.")
        print("=================================\n")

    def test_get_all_categories(self):
        response = get("/categories")
        self.print_results("GET /categories", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_category_by_id_json(self):
        response = get(f"/categories/{self.category_id}", headers={"Accept": "application/json"})
        self.print_results("GET /categories/:id (JSON format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_get_category_by_id_xml(self):
        response = get(f"/categories/{self.category_id}", headers={"Accept": "application/xml"})
        self.print_results("GET /categories/:id (XML format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/xml")

    def test_get_non_existent_category(self):
        response = get("/categories/999999")
        self.print_results("GET /categories/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_post_category_json(self):
        new_category = {"title": "New Category", "description": "New Desc"}
        response = post("/categories", new_category, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories (JSON format)", 201, response.status_code)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_post_category_xml(self):
        xml_payload = """<category><title>New Category</title><description>New Desc</description></category>"""
        response = post("/categories", xml_payload, headers={"Content-Type": "application/xml"})
        self.print_results("POST /categories (XML format)", 201, response.status_code)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Content-Type"], "application/xml")

    def test_post_category_empty_body(self):
        response = post("/categories", {}, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories (empty body)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_post_category_invalid_field_type(self):
        new_category = {"title": "Invalid Category", "priority": "not an integer"}
        response = post("/categories", new_category, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories (invalid field type)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_put_category_json(self):
        update_data = {"title": "Updated Title", "description": "Updated Desc"}
        response = put(f"/categories/{self.category_id}", update_data, headers={"Content-Type": "application/json"})
        self.print_results("PUT /categories/:id (JSON format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_put_category_xml(self):
        xml_payload = """<category><title>Updated Title</title><description>Updated Desc</description></category>"""
        response = put(f"/categories/{self.category_id}", xml_payload, headers={"Content-Type": "application/xml"})
        self.print_results("PUT /categories/:id (XML format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_put_category_empty_body(self):
        response = put(f"/categories/{self.category_id}", {}, headers={"Content-Type": "application/json"})
        self.print_results("PUT /categories/:id (empty body)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_put_non_existent_category(self):
        update_data = {"title": "Ghost Category"}
        response = put("/categories/999999", update_data, headers={"Content-Type": "application/json"})
        self.print_results("PUT /categories/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_delete_category(self):
        response = delete(f"/categories/{self.category_id}")
        self.print_results("DELETE /categories/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_delete_non_existent_category(self):
        response = delete("/categories/999999")
        self.print_results("DELETE /categories/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_post_malformed_json(self):
        malformed_data = '{"title": "Broken JSON", "description": "Oops"'  # Missing closing bracket
        response = post("/categories", malformed_data, headers={"Content-Type": "application/json"})
        self.print_results("POST /categories (malformed JSON)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_post_malformed_xml(self):
        malformed_xml = "<category><title>Broken XML<title></category>"  # Malformed XML
        response = post("/categories", malformed_xml, headers={"Content-Type": "application/xml"})
        self.print_results("POST /categories (malformed XML)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
