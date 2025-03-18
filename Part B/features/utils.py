import requests
import json

def make_request(context, method, endpoint, data=None):
    """Make HTTP request to the API with error handling"""
    try:
        url = f"{context.base_url}{endpoint}"

        if method == "GET":
            response = requests.get(url, headers=context.headers)
        elif method == "POST":
            response = requests.post(url, headers=context.headers, data=json.dumps(data))
        elif method == "PUT":
            response = requests.put(url, headers=context.headers, data=json.dumps(data))
        elif method == "DELETE":
            response = requests.delete(url, headers=context.headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response
    except requests.exceptions.ConnectionError:
        raise Exception("Failed to connect to the API service. Is it running?")

def reset_system_state(context):
    """Reset the system to initial state"""
    try:
        # Delete all todos
        response = make_request(context, "GET", "/todos")
        if response.status_code == 200:
            todos = response.json()
            for todo in todos:
                make_request(context, "DELETE", f"/todos/{todo['id']}")

        # Delete all categories
        response = make_request(context, "GET", "/categories")
        if response.status_code == 200:
            categories = response.json()
            for category in categories:
                make_request(context, "DELETE", f"/categories/{category['id']}")

        # Delete all projects
        response = make_request(context, "GET", "/projects")
        if response.status_code == 200:
            projects = response.json()
            for project in projects:
                make_request(context, "DELETE", f"/projects/{project['id']}")
    except:
        raise Exception("Failed to reset system state")

def validate_response_schema(response_data, expected_fields):
    """Validate that response contains required fields"""
    for field in expected_fields:
        if field not in response_data:
            raise AssertionError(f"Response missing required field: {field}")
