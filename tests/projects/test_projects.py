import unittest
from tests.utils.api_client import get, post, delete

class TestProjectsAPI(unittest.TestCase):

    def test_get_all_projects(self):
        response = get("/projects")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
