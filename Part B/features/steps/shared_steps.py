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
            "title": json.loads(row['title']),
            "doneStatus": row['doneStatus'] == 'true',
            "description": json.loads(row['description'])
        }
        response = make_request(context, "POST", "/todos", todo_data)
        assert response.status_code == 201, f"Failed to create todo: {response.text}"

@given('a ToDo with ID equal to {id} exists')
def verify_todo_exists(context, id):
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code == 200, f"Todo with ID {id} does not exist"

@then('the response status should be {status:d}')
def verify_response_status(context, status):
    assert context.response.status_code == status, \
        f"Expected status code {status} but got {context.response.status_code}"

@then('the response JSON should contain an error message "{message}"')
def verify_error_message(context, message):
    response_data = context.response.json()
    assert 'message' in response_data or 'errorMessages' in response_data, "Error message missing"
    actual_message = response_data.get('message', response_data.get('errorMessages', [None])[0])
    assert message in str(actual_message), f"Expected error message '{message}' but got '{actual_message}'"
