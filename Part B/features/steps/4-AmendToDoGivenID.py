from behave import given, when, then
from utils import make_request
import json

@given('the server is running')
def verify_server_running(context):
    response = make_request(context, "GET", "/todos")
    assert response.status_code in [200, 404], "Server is not running"

@given('a ToDo with ID equal to {id} exists with title "{title}", doneStatus {doneStatus}, and description "{description}"')
def setup_existing_todo(context, id, title, doneStatus, description):
    # Create the todo if it doesn't exist
    todo_data = {
        "title": json.loads(title),
        "doneStatus": doneStatus.lower() == 'true',
        "description": json.loads(description)
    }

    # Check if todo exists
    response = make_request(context, "GET", f"/todos/{id}")
    if response.status_code == 404:
        # Create new todo
        response = make_request(context, "POST", "/todos", todo_data)
        assert response.status_code == 201, f"Failed to create todo: {response.text}"

@given('a ToDo with ID equal to {id} does not exist')
def verify_todo_not_exists(context, id):
    response = make_request(context, "GET", f"/todos/{id}")
    assert response.status_code == 404, f"Todo with ID {id} exists but should not"

@when('the user requests to update the ToDo with id {id} setting title to {title}, doneStatus to {doneStatus}, and description to {description}')
def update_todo_all_fields(context, id, title, doneStatus, description):
    update_data = {
        "title": json.loads(title),
        "doneStatus": doneStatus.lower() == 'true',
        "description": json.loads(description)
    }
    context.response = make_request(context, "PUT", f"/todos/{id}", update_data)

@when('the user requests to update the ToDo with id {id} setting only description to {description}')
def update_todo_partial(context, id, description):
    update_data = {
        "description": json.loads(description)
    }
    context.response = make_request(context, "PUT", f"/todos/{id}", update_data)
