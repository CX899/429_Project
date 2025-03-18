from behave import given, when, then
from utils import make_request
import json

@given('the system has been reset to its initial state')
def reset_system(context):
    response = make_request(context, "GET", "/todos")
    if response.status_code == 200:
        for todo in response.json():
            make_request(context, "DELETE", f"/todos/{todo['id']}")

@given('the system contains the following todos')
def setup_todos(context):
    # Create the todos from the table
    for row in context.table:
        todo_data = {
            "title": json.loads(row['title']),
            "doneStatus": row['doneStatus'].lower() == 'true',
            "description": json.loads(row['description'])
        }
        response = make_request(context, "POST", "/todos", todo_data)
        assert response.status_code == 201, f"Failed to create todo: {response.text}"

@given('a ToDo with ID equal to {id} exists')
def verify_todo_exists(context, id):
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code == 200, f"Todo with ID {id} does not exist"

@given('a ToDo with ID equal to {id} does not exist or the ID format is invalid')
def verify_todo_invalid(context, id):
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code in [404, 400], f"Expected todo {id} to not exist or be invalid"

@when('the user sends a DELETE request to "/todos/{id}"')
def delete_todo(context, id):
    context.response = make_request(context, "DELETE", f"/todos/{id}")

@then('the ToDo with id {id} is successfully deleted')
def verify_deletion(context, id):
    assert context.response.status_code == 204, "Delete operation failed"

    # Verify todo no longer exists
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code == 404, f"Todo with ID {id} still exists"

@then('the user is notified of the completion of the deletion operation')
def verify_deletion_notification(context):
    assert context.response.status_code == 204, "Expected 204 status code"

@then('the response JSON should contain an error message "{message}"')
def verify_error_message(context, message):
    response_data = context.response.json()
    assert 'message' in response_data or 'errorMessages' in response_data, "Error message missing"
    actual_message = response_data.get('message', response_data.get('errorMessages', [None])[0])
    assert message == str(actual_message), f"Expected error message '{message}' but got '{actual_message}'"

@then('the response status should be {status:d}')
def verify_response_status(context, status):
    assert context.response.status_code == status, \
        f"Expected status code {status} but got {context.response.status_code}"
