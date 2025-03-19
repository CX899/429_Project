import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, is_in
from features.steps.test_utils import setup_test_todos, get_mapped_id

@given('the system contains the following todos')
def step_setup_todos(context):
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

@given('a ToDo with ID equal to {id} does not exist or the ID format is invalid')
def step_verify_todo_nonexistent(context, id):
    if not id.isdigit():
        print(f"ID {id} is not a valid numeric format")
        return
    
    actual_id = get_mapped_id(context, id)
    
    response = requests.get(f"{context.base_url}/todos/{actual_id}")
    
    if response.status_code == 200:
        delete_response = requests.delete(f"{context.base_url}/todos/{actual_id}")
        assert delete_response.status_code in [200, 204], f"Failed to delete todo with ID {actual_id}"
        print(f"Deleted existing todo with ID {actual_id} for test setup")

@then('the response JSON should contain a todo with id "{id}"')
def step_verify_todo_id(context, id):
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        assert False, "Response is not valid JSON"
    
    actual_id = get_mapped_id(context, id)
    
    if isinstance(context.response_data, dict) and 'todos' in context.response_data:
        todos = context.response_data['todos']
        found = False
        for todo in todos:
            if str(todo.get('id')) == actual_id:
                found = True
                break
        assert found, f"No todo with ID {actual_id} found in response"
    elif isinstance(context.response_data, dict) and 'id' in context.response_data:
        assert_that(str(context.response_data.get('id')), equal_to(actual_id))
    else:
        assert False, f"Response doesn't contain a todo with ID {actual_id}: {context.response_data}"
    
    print(f"Verified response contains todo with ID {actual_id}")