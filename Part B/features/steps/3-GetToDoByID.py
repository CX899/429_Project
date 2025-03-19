from behave import given, when, then
from utils import make_request
import json
# Shared steps will be automatically loaded by behave

@given('a ToDo with ID equal to {id} does not exist or the ID format is invalid')
def verify_todo_nonexistent(context, id):
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code in [404, 400], f"Expected todo {id} to not exist or be invalid"

@then('the response JSON should include the todo with id "{id}" with title "{title}", doneStatus "{doneStatus}" and description "{description}"')
def verify_todo_details(context, id, title, doneStatus, description):
    response_data = context.response.json()
    assert str(response_data['id']) == id, "ID mismatch"
    assert response_data['title'] == json.loads(title), "Title mismatch"
    assert str(response_data['doneStatus']).lower() == doneStatus.lower(), "DoneStatus mismatch"
    assert response_data['description'] == json.loads(description), "Description mismatch"

@then('the response JSON should contain an error message "{message}"')
def verify_error_message(context, message):
    response_data = context.response.json()
    assert 'message' in response_data or 'errorMessages' in response_data, "Error message missing in response"
    actual_message = response_data.get('message', response_data.get('errorMessages', [None])[0])
    assert message in str(actual_message), f"Expected error message '{message}' but got '{actual_message}'"
