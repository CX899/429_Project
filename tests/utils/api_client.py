import requests
from tests.utils.config import BASE_URL

def get(endpoint):
    """Send a GET request."""
    return requests.get(f"{BASE_URL}{endpoint}")

def post(endpoint, json_body):
    """Send a POST request."""
    return requests.post(f"{BASE_URL}{endpoint}", json=json_body)

def put(endpoint, json_body):
    """Send a PUT request."""
    return requests.put(f"{BASE_URL}{endpoint}", json=json_body)

def delete(endpoint):
    """Send a DELETE request."""
    return requests.delete(f"{BASE_URL}{endpoint}")

def head(endpoint):
    """Send a HEAD request."""
    return requests.head(f"{BASE_URL}{endpoint}")
