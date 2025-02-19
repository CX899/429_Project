import unittest
from tests.utils.api_client import get, post, delete

class TestTodosAPI(unittest.TestCase):

    def test_get_all_todos(self):
        response = get("/todos")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
