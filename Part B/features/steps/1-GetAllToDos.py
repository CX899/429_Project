"""
Step definitions specific to retrieving all ToDos.
"""
import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, has_length, greater_than_or_equal_to

@given('the API contains todos data')
def step_verify_api_has_data(context):
    url = context.base_url + "/todos"
    response = requests.get(url)
    
    assert response.status_code == 200, f"API returned status {response.status_code}"
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, "API response is not valid JSON"
        
    if isinstance(data, dict) and 'todos' in data:
        todos = data['todos']
    else:
        todos = data
        
    assert len(todos) > 0, "API returned empty todos list"
    
    context.todos = todos
    print(f"API has {len(todos)} todos available")

@given('a filter where "{filter_key}" equals "{filter_value}"')
def step_set_filter(context, filter_key, filter_value):
    context.filter_key = filter_key
    context.filter_value = filter_value

@then('the response JSON should contain only todos where {filter_key} equals "{filter_value}"')
def step_verify_filtered_todos(context, filter_key, filter_value):
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'todos' in context.response_data:
        todos = context.response_data['todos']
    else:
        todos = context.response_data
    
    expected_value = filter_value
    if filter_value in ['true', 'false']:
        expected_value = filter_value.lower()
    elif filter_value.startswith('"') and filter_value.endswith('"'):
        expected_value = json.loads(filter_value)
    
    print(f"Checking {len(todos)} todos for filter {filter_key}={expected_value}")
    
    if len(todos) > 0:
        for todo in todos:
            actual_value = str(todo.get(filter_key)).lower() if filter_key in todo else None
            if filter_value.startswith('"') and filter_value.endswith('"'):
                assert str(actual_value) == str(expected_value), \
                    f"Todo does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"
            else:
                assert str(actual_value).lower() == str(expected_value).lower(), \
                    f"Todo does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"