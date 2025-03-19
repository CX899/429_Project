"""
Step definitions for ToDo API tests.
"""
import json
import requests
from behave import given, when, then
from hamcrest import assert_that, equal_to, has_length, greater_than_or_equal_to

@given('the API contains todos data')
def step_verify_api_has_data(context):
    """
    Verify that the API has some todos data for testing.
    This is a more flexible approach than requiring specific todos.
    """
    url = context.base_url + "/todos"
    response = requests.get(url)
    
    # Verify we got a successful response
    assert response.status_code == 200, f"API returned status {response.status_code}"
    
    # Parse the response
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, "API response is not valid JSON"
        
    # Get the todos list
    if isinstance(data, dict) and 'todos' in data:
        todos = data['todos']
    else:
        todos = data
        
    # Make sure there are some todos
    assert len(todos) > 0, "API returned empty todos list"
    
    # Save the todos for later steps
    context.todos = todos
    print(f"API has {len(todos)} todos available")


@given('a filter where "{filter_key}" equals "{filter_value}"')
def step_set_filter(context, filter_key, filter_value):
    """Store filter information for later use"""
    context.filter_key = filter_key
    context.filter_value = filter_value


@when('the user sends a GET request to "{endpoint}"')
def step_send_get_request(context, endpoint):
    """Send a GET request to the specified endpoint"""
    url = context.base_url + endpoint
    context.response = requests.get(url)
    
    # Debugging: print response details
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")  # Print first 100 chars


@when('the user sends a {method} request to "{invalid_endpoint}"')
def step_send_request_with_method(context, method, invalid_endpoint):
    """Send a request with the specified HTTP method to the endpoint"""
    url = context.base_url + invalid_endpoint
    context.response = getattr(requests, method.lower())(url)
    
    # Debugging: print response details
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")  # Print first 100 chars


@then('the response status should be {status:d}')
def step_verify_status_code(context, status):
    """Verify the HTTP status code of the response"""
    assert_that(context.response.status_code, equal_to(status))


@then('the response contains a list of todos')
def step_verify_todos_list(context):
    """Verify that the response contains a list of todos"""
    # Try to parse as JSON
    try:
        response_data = context.response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"
    
    # If response is a dictionary with todos as a key, extract the todos list
    if isinstance(response_data, dict) and 'todos' in response_data:
        todos = response_data['todos']
    else:
        todos = response_data
    
    # Verify it's a list
    assert isinstance(todos, list), f"Expected a list of todos, but got {type(todos)}"
    
    # Verify the list is not empty
    assert_that(len(todos), greater_than_or_equal_to(1))
    
    # Print some info about the todos
    print(f"Response contains {len(todos)} todos")
    if len(todos) > 0:
        print(f"First todo: {todos[0]}")


@then('the response JSON should contain only todos where {filter_key} equals "{filter_value}"')
def step_verify_filtered_todos(context, filter_key, filter_value):
    """Verify that the response contains only todos matching the filter criteria"""
    # Try to parse as JSON
    try:
        response_data = context.response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"
    
    # If response is a dictionary with todos as a key, extract the todos list
    if isinstance(response_data, dict) and 'todos' in response_data:
        todos = response_data['todos']
    else:
        todos = response_data
    
    # Handle boolean and string filter values
    expected_value = filter_value
    if filter_value in ['true', 'false']:
        expected_value = filter_value.lower()
    elif filter_value.startswith('"') and filter_value.endswith('"'):
        expected_value = json.loads(filter_value)
    
    print(f"Checking {len(todos)} todos for filter {filter_key}={expected_value}")
    
    # If there are todos, check they match the filter
    if len(todos) > 0:
        for todo in todos:
            actual_value = str(todo.get(filter_key)).lower() if filter_key in todo else None
            if filter_value.startswith('"') and filter_value.endswith('"'):
                # For string values, just compare strings
                assert str(actual_value) == str(expected_value), \
                    f"Todo does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"
            else:
                # For boolean values, compare lowercase strings
                assert str(actual_value).lower() == str(expected_value).lower(), \
                    f"Todo does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"