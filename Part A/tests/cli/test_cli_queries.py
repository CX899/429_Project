import unittest
import subprocess

class TestCommandLineQueries(unittest.TestCase):
    """Tests for command line interface queries"""

    def setUp(self):
        """Verify API is running"""
        result = subprocess.run(['curl', 'http://localhost:4567'],
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_cli_get_todos(self):
        """Test GET /todos via curl"""
        result = subprocess.run(
            ['curl', 'http://localhost:4567/todos'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"todos":', result.stdout)

    def test_cli_create_todo(self):
        """Test POST /todos via curl"""
        cmd = [
            'curl', '-X', 'POST',
            'http://localhost:4567/todos',
            '-H', 'Content-Type: application/json',
            '-d', '{"title":"CLI Todo"}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
