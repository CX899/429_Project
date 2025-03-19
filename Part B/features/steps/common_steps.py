"""
Common step definitions shared across feature files.
"""
import json
import requests
from behave import given, when, then
from hamcrest import assert_that, equal_to, has_item, contains_string, has_key
from features.steps.test_utils import get_mapped_id, map_endpoint_id, verify_error_message

@given('the system is running')
def step_verify_system_running(context):
    url = context.base_url + "/todos"
    response = requests.get(url)
    assert response.status_code == 200, f"API returned status {response.status_code}, system may not be running"
    print("System is running and API is accessible")

@when('the user sends a GET request to "{endpoint}"')
def step_send_get_request(context, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    context.response = requests.get(url)
    
    print(f"Sent GET request to {url}")
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a GET request to "{endpoint}"')
def step_send_get_request_to_endpoint(context, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    
    print(f"Sending GET request to {url}")
    
    context.response = requests.get(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print(f"Response is not JSON or is empty: {context.response.text[:200]}...")

@when('the user sends a {method} request to "{endpoint}"')
def step_send_request_with_method(context, method, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    
    print(f"Sending {method} request to {url}")
    
    context.response = getattr(requests, method.lower())(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print(f"Response is not JSON or is empty: {context.response.text[:200]}...")

@when('I send a DELETE request to "{endpoint}"')
def step_send_delete_request(context, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    
    print(f"Sending DELETE request to {url}")
    
    context.response = requests.delete(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print(f"Response is not JSON or is empty: {context.response.text[:200]}...")

@when('the user sends a POST request to "{endpoint}" with this JSON body')
def step_send_post_request_with_json(context, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    headers = {"Content-Type": "application/json"}
    
    json_body = context.todo_body if hasattr(context, 'todo_body') else context.category_body
    
    context.response = requests.post(url, json=json_body, headers=headers)
    
    print(f"POST to {url}")
    print(f"Request body: {json_body}")
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('the user sends a POST request to "{endpoint}" with this invalid body')
def step_send_post_request_with_invalid_json(context, endpoint):
    # Special case for the bug scenario - POST to existing todo ID
    if hasattr(context, 'special_endpoint') and context.special_endpoint:
        endpoint = context.special_endpoint
        print(f"Using special endpoint for bug scenario: {endpoint}")
    
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    headers = {"Content-Type": "application/json"}
    
    json_body = context.todo_body if hasattr(context, 'todo_body') else context.category_body
    
    context.response = requests.post(url, json=json_body, headers=headers)
    
    print(f"POST to {url}")
    print(f"Request body: {json_body}")
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a {method} request to "{endpoint}" with the updated data')
def step_send_request_with_updated_data(context, method, endpoint):
    # Map the endpoint if it contains an ID
    mapped_endpoint = map_endpoint_id(context, endpoint)
    
    url = context.base_url + mapped_endpoint
    headers = {"Content-Type": "application/json"}
    
    json_body = context.category_body if hasattr(context, 'category_body') else context.todo_body
    
    print(f"Sending {method} request to {url} with body: {json_body}")
    
    context.response = getattr(requests, method.lower())(url, json=json_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a {method} request to "{endpoint}" with the partial data')
def step_send_request_with_partial_data(context, method, endpoint):
    step_send_request_with_updated_data(context, method, endpoint)

@when('the user sends a POST request to "{endpoint}" with this data')
def step_send_post_request_with_category_data(context, endpoint):
    step_send_post_request_with_json(context, endpoint)

@when('the user sends a POST request to "{endpoint}" with this incomplete data')
def step_send_post_request_with_incomplete_data(context, endpoint):
    step_send_post_request_with_json(context, endpoint)

@then('the response status should be {status:d}')
def step_verify_status_code(context, status):
    assert_that(context.response.status_code, equal_to(status))
    print(f"Verified response status code is {status}")

@then('the response JSON should contain an error message mentioning "{message}"')
def step_verify_error_message_contains(context, message):
    assert verify_error_message(context, [message]), f"Error message not found mentioning: {message}"
    print(f"Verified response contains error message mentioning: {message}")

@then('the response JSON should contain an error message "{message}"')
def step_verify_error_message_exact(context, message):
    step_verify_error_message_contains(context, message)

@then('the response should include an error message indicating invalid ID format')
def step_verify_invalid_id_error(context):
    assert context.response.status_code == 404, \
        f"Expected 404 status code for invalid ID format, got {context.response.status_code}"
    
    error_phrases = ["invalid", "format", "guid", "malformed", "could not find"]
    assert verify_error_message(context, error_phrases), \
        f"Error message about invalid ID format not found in response"
    print("Verified response contains invalid ID format error message")

@then('the response should include an error message indicating category not found')
def step_verify_category_not_found_error(context):
    assert context.response.status_code == 404, \
        f"Expected 404 status code for category not found, got {context.response.status_code}"
    
    error_phrases = ["not found", "could not find", "doesn't exist", "does not exist"]
    assert verify_error_message(context, error_phrases), \
        f"Error message about category not found not found in response"
    print("Verified response contains category not found error message")
    
@then('the response contains a list of todos')
def step_verify_todos_list(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'todos' in context.response_data:
        todos = context.response_data['todos']
    else:
        todos = context.response_data
    
    assert isinstance(todos, list), f"Expected a list of todos, but got {type(todos)}"
    
    print(f"Response contains {len(todos)} todos")
    if len(todos) > 0:
        print(f"First todo: {todos[0]}")

@then('the response contains a list of categories')
def step_verify_categories_list(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'categories' in context.response_data:
        categories = context.response_data['categories']
    else:
        categories = context.response_data
    
    assert isinstance(categories, list), f"Expected a list of categories, but got {type(categories)}"
    
    print(f"Response contains {len(categories)} categories")
    if len(categories) > 0:
        print(f"First category: {categories[0]}")

@then('the response JSON should contain an error message indicating invalid input')
def step_verify_error_for_invalid_input(context):
    error_phrases = ["error", "invalid", "missing", "required", "mandatory"]
    assert verify_error_message(context, error_phrases), \
        f"Error message about invalid input not found in response"
    print("Verified response contains error message about invalid input")

@then('the response JSON should include an error message indicating missing required fields')
def step_verify_missing_required_fields_error(context):
    assert context.response.status_code == 400, \
        f"Expected 400 status code for missing required fields, got {context.response.status_code}"
    
    error_phrases = ["required", "mandatory", "missing", "field is mandatory", "title"]
    assert verify_error_message(context, error_phrases), \
        f"Error message about missing required fields not found in response"
    print("Verified response contains error message about missing required fields")

@then('the response contains a list of projects')
def step_verify_projects_list(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
    else:
        projects = context.response_data
    
    assert isinstance(projects, list), f"Expected a list of projects, but got {type(projects)}"
    
    print(f"Response contains {len(projects)} projects")
    if len(projects) > 0:
        print(f"First project: {projects[0]}")