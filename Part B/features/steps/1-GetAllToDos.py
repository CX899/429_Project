from behave import given, when, then
from utils import make_request, reset_system_state
import json

@given('the system contains the following todos')
def setup_initial_todos(context):
    # Reset system state first
    reset_system_state(context)

    # Create the todos from the table
    for row in context.table:
        todo_data = {
            "title": json.loads(row['title']),  # Remove quotes from string
            "doneStatus": row['doneStatus'] == 'true',
            "description": json.loads(row['description'])
        }
        response = make_request(context, "POST", "/todos", todo_data)
        assert response.status_code == 201, f"Failed to create todo: {response.text}"

@when('the user sends a {method} request to "{endpoint}"')
def send_request(context, method, endpoint):
    context.response = make_request(context, method, endpoint)

@then('the response status should be {status:d}')
def verify_response_status(context, status):
    assert context.response.status_code == status, \
        f"Expected status code {status} but got {context.response.status_code}"

@then('the response JSON should include the following todos')
def verify_response_todos(context):
    response_data = context.response.json()
    expected_todos = []

    for row in context.table:
        expected_todo = {
            "title": json.loads(row['title']),
            "doneStatus": row['doneStatus'] == 'true',
            "description": json.loads(row['description'])
        }
        expected_todos.append(expected_todo)

    # Verify each expected todo exists in response
    for expected_todo in expected_todos:
        found = False
        for actual_todo in response_data:
            if (actual_todo['title'] == expected_todo['title'] and
                actual_todo['doneStatus'] == expected_todo['doneStatus'] and
                actual_todo['description'] == expected_todo['description']):
                found = True
                break
        assert found, f"Expected todo not found in response: {expected_todo}"

@given('a filter where "{filter_key}" equals "{filter_value}"')
def setup_filter(context, filter_key, filter_value):
    context.filter_key = filter_key
    context.filter_value = json.loads(filter_value) if filter_value.startswith('"') else filter_value

@then('the response JSON should contain only todos where {filter_key} equals "{filter_value}"')
def verify_filtered_todos(context, filter_key, filter_value):
    response_data = context.response.json()
    filter_value = json.loads(filter_value) if filter_value.startswith('"') else filter_value

    for todo in response_data:
        assert str(todo[filter_key]) == str(filter_value), \
            f"Todo does not match filter criteria: {todo}"
