from behave import given, when, then
from utils import make_request
import json

@given('the system is running')
def verify_system_running(context):
    # Make a simple request to verify system is up
    response = make_request(context, "GET", "/todos")
    assert response.status_code in [200, 404], "System is not running"

@given('the user has a valid JSON body for a new ToDo with')
def setup_valid_todo_data(context):
    row = context.table[0]
    context.todo_data = {
        "title": json.loads(row['title']),
        "doneStatus": row['doneStatus'].lower() == 'true',
        "description": json.loads(row['description'])
    }

@given('the user has a valid JSON body for a new ToDo without an "id" field')
def setup_todo_data_without_id(context):
    row = context.table[0]
    context.todo_data = {
        "title": json.loads(row['title']),
        "doneStatus": row['doneStatus'].lower() == 'true',
        "description": json.loads(row['description'])
    }

@given('the user has an invalid JSON body for a new ToDo with "{issue}"')
def setup_invalid_todo_data(context, issue):
    if issue == "missing required fields":
        context.todo_data = {"description": "Missing title and doneStatus"}
    elif issue == "title is null":
        context.todo_data = {
            "title": None,
            "doneStatus": False,
            "description": "Title is null"
        }
    elif issue == "doneStatus is not a boolean value":
        context.todo_data = {
            "title": "Invalid doneStatus",
            "doneStatus": "not a boolean",
            "description": "Invalid doneStatus value"
        }

@when('the user sends a POST request to "{endpoint}" with this JSON body')
def send_post_request(context, endpoint):
    context.response = make_request(context, "POST", endpoint, context.todo_data)

@when('the user sends a POST request to "{endpoint}" with this invalid body')
def send_post_request_invalid(context, endpoint):
    context.response = make_request(context, "POST", endpoint, context.todo_data)

@then('the response JSON should contain a new ToDo with the specified title, doneStatus, and description')
def verify_todo_creation(context):
    response_data = context.response.json()
    assert response_data['title'] == context.todo_data['title'], "Title mismatch"
    assert response_data['doneStatus'] == context.todo_data['doneStatus'], "DoneStatus mismatch"
    assert response_data['description'] == context.todo_data['description'], "Description mismatch"

@then('the response JSON should contain a unique "id"')
def verify_todo_id(context):
    response_data = context.response.json()
    assert 'id' in response_data, "ID field missing in response"
    assert response_data['id'] is not None, "ID is null"

@then('the response JSON should contain a newly generated "id" that does not match any existing ToDo')
def verify_unique_id(context):
    response_data = context.response.json()
    assert 'id' in response_data, "ID field missing in response"
    assert response_data['id'] is not None, "ID is null"

    # Get all todos to verify ID uniqueness
    all_todos = make_request(context, "GET", "/todos").json()
    id_count = sum(1 for todo in all_todos if todo['id'] == response_data['id'])
    assert id_count == 1, "Generated ID is not unique"

@then('the response JSON should contain an error message indicating invalid input')
def verify_error_message(context):
    response_data = context.response.json()
    assert 'message' in response_data or 'errorMessages' in response_data, "Error message missing in response"
