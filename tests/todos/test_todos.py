import unittest
from tests.utils.api_client import get, post, put, delete, head

class TestTodosAPI(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test"""
        # Verify system is running
        response = get("/")
        self.assertEqual(response.status_code, 200)

        # Save initial state
        self.initial_state = get("/todos").json()

        # Create test data
        self.test_todo = {"title": "Test Todo", "description": "Test Description"}
        response = post("/todos", self.test_todo, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.todo_id = response.json()["id"]

    def tearDown(self):
        """Restore system to initial state"""
        # Delete test data
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

    def test_get_all_todos(self):
        response = get("/todos")
        self.print_results("GET /todos", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_get_todo_by_id_json(self):
        response = get(f"/todos/{self.todo_id}", headers={"Accept": "application/json"})
        self.print_results("GET /todos/:id (JSON format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_get_todo_by_id_xml(self):
        response = get(f"/todos/{self.todo_id}", headers={"Accept": "application/xml"})
        self.print_results("GET /todos/:id (XML format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/xml")

    def test_get_non_existent_todo(self):
        response = get("/todos/999999")
        self.print_results("GET /todos/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_post_todo_json(self):
        new_todo = {"title": "New Todo", "description": "Valid Description"}
        response = post("/todos", new_todo, headers={"Content-Type": "application/json"})
        self.print_results("POST /todos (JSON format)", 201, response.status_code)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_post_todo_xml(self):
        """Test creating todo with XML payload"""
        xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
            <todo>
                <title>New Todo</title>
                <description>Valid Description</description>
            </todo>"""
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/xml"
        }
        response = post("/todos", xml_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        # Check if response is actually XML
        self.assertTrue(
            response.headers["Content-Type"].startswith("application/xml") or
            response.headers["Content-Type"].startswith("application/json")
        )

    def test_post_todo_empty_body(self):
        response = post("/todos", {}, headers={"Content-Type": "application/json"})
        self.print_results("POST /todos (empty body)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_post_todo_invalid_field_type(self):
        new_todo = {"title": "Invalid Todo", "priority": "not an integer"}
        response = post("/todos", new_todo, headers={"Content-Type": "application/json"})
        self.print_results("POST /todos (invalid field type)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_put_todo_json(self):
        update_data = {"title": "Updated Title", "description": "Updated Desc"}
        response = put(f"/todos/{self.todo_id}", update_data, headers={"Content-Type": "application/json"})
        self.print_results("PUT /todos/:id (JSON format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_put_todo_xml(self):
        xml_payload = """<todo><title>Updated Title</title><description>Updated Desc</description></todo>"""
        response = put(f"/todos/{self.todo_id}", xml_payload, headers={"Content-Type": "application/xml"})
        self.print_results("PUT /todos/:id (XML format)", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_put_todo_empty_body(self):
        response = put(f"/todos/{self.todo_id}", {}, headers={"Content-Type": "application/json"})
        self.print_results("PUT /todos/:id (empty body)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_put_non_existent_todo(self):
        update_data = {"title": "Ghost Todo"}
        response = put("/todos/999999", update_data, headers={"Content-Type": "application/json"})
        self.print_results("PUT /todos/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_delete_todo(self):
        response = delete(f"/todos/{self.todo_id}")
        self.print_results("DELETE /todos/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_delete_non_existent_todo(self):
        response = delete("/todos/999999")
        self.print_results("DELETE /todos/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)

    def test_post_malformed_json(self):
        malformed_data = '{"title": "Broken JSON", "description": "Oops"'  # Missing closing bracket
        response = post("/todos", malformed_data, headers={"Content-Type": "application/json"})
        self.print_results("POST /todos (malformed JSON)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_post_malformed_xml(self):
        malformed_xml = "<todo><title>Broken XML<title></todo>"  # Malformed XML
        response = post("/todos", malformed_xml, headers={"Content-Type": "application/xml"})
        self.print_results("POST /todos (malformed XML)", 400, response.status_code)
        self.assertEqual(response.status_code, 400)

    def test_head_all_todos(self):
        """Test HEAD request for all todos"""
        response = head("/todos")
        self.print_results("HEAD /todos", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_head_todo_by_id(self):
        """Test HEAD request for specific todo"""
        response = head(f"/todos/{self.todo_id}")
        self.print_results("HEAD /todos/:id", 200, response.status_code)
        self.assertEqual(response.status_code, 200)

    def test_head_non_existent_todo(self):
        """Test HEAD request for non-existent todo"""
        response = head("/todos/999999")
        self.print_results("HEAD /todos/999999", 404, response.status_code)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
