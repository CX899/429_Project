import requests
from tests.utils.config import BASE_URL

def get(endpoint, headers=None):
    """Send a GET request."""
    return requests.get(f"{BASE_URL}{endpoint}", headers=headers)

def post(endpoint, data=None, headers=None):
    """Send a POST request."""
    if headers and headers.get("Content-Type") == "application/xml":
        return requests.post(f"{BASE_URL}{endpoint}", data=data, headers=headers)
    return requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)

def put(endpoint, data=None, headers=None):
    """Send a PUT request."""
    if headers and headers.get("Content-Type") == "application/xml":
        return requests.put(f"{BASE_URL}{endpoint}", data=data, headers=headers)
    return requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)

def delete(endpoint, headers=None):
    """Send a DELETE request."""
    return requests.delete(f"{BASE_URL}{endpoint}", headers=headers)

def head(endpoint, headers=None):
    """Send a HEAD request."""
    return requests.head(f"{BASE_URL}{endpoint}", headers=headers)
