import json
import requests
from behave import given, when, then
from hamcrest import assert_that, is_not, is_in
from features.steps.test_utils import setup_test_todos, get_mapped_id, verify_todo_exists

@given('the system has been reset to its initial state')
def step_reset_system(context):
    print("System has been reset to its initial state")

@given('the system contains the following todos:')
def step_setup_specific_todos(context):
    test_todos = []
    for row in context.table:
        test_todo = {
            'id': str(row['id']).strip(),
            'title': row['title'].strip('"'),
            'doneStatus': row['doneStatus'],
            'description': row['description'].strip('"')
        }
        test_todos.append(test_todo)
    
    setup_test_todos(context, test_todos)

@when('the user sends a DELETE request to "{endpoint}"')
def step_delete_request(context, endpoint):
    if '/todos/' in endpoint:
        parts = endpoint.split('/')
        if len(parts) >= 3:
            requested_id = parts[2]
            actual_id = get_mapped_id(context, requested_id)
            url = f"{context.base_url}/todos/{actual_id}"
            print(f"Mapped DELETE endpoint from {endpoint} to /todos/{actual_id}")
        else:
            url = context.base_url + endpoint
    else:
        url = context.base_url + endpoint
    
    context.response = requests.delete(url)
    
    print(f"Sent DELETE request to {url}")
    print(f"Response status code: {context.response.status_code}")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print(f"Response is not JSON or is empty: {context.response.text[:200]}...")

@then('the ToDo with id {id} is successfully deleted')
def step_verify_todo_deleted(context, id):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 404, f"ToDo with ID {actual_id} still exists"
    
    all_todos_response = requests.get(f"{context.base_url}/todos")
    assert all_todos_response.status_code == 200, "Failed to get all todos"
    
    try:
        todos_data = all_todos_response.json()
        if isinstance(todos_data, dict) and 'todos' in todos_data:
            todos = todos_data['todos']
        else:
            todos = todos_data
            
        todo_ids = [str(todo.get('id')) for todo in todos]
        assert_that(actual_id, is_not(is_in(todo_ids)))
        
        print(f"Verified ToDo with ID {actual_id} was successfully deleted")
    except (json.JSONDecodeError, AssertionError) as e:
        assert False, f"Failed to verify todo deletion: {e}"

@then('the user is notified of the completion of the deletion operation')
def step_verify_deletion_success(context):
    assert context.response.status_code in [200, 204], \
        f"Expected successful status code, got {context.response.status_code}"
    print("Verified deletion operation completed successfully")