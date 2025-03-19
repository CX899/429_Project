from behave import given, when, then
from utils import make_request
import json

@given('the system has been reset to its initial state')
def reset_system(context):
    response = make_request(context, "GET", "/todos")
    if response.status_code == 200:
        for todo in response.json():
            make_request(context, "DELETE", f"/todos/{todo['id']}")

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
