"""
Step definitions for retrieving a specific ToDo by ID.
"""
import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, is_in

@given('the system contains the following todos')
def step_setup_todos(context):
    response = requests.get(f"{context.base_url}/todos")
    existing_todos = {}
    
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and 'todos' in data:
                todos_list = data['todos']
            else:
                todos_list = data
                
            existing_todos = {str(todo.get('id')): todo for todo in todos_list if todo.get('id')}
            print(f"Found {len(existing_todos)} existing todos")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing existing todos: {e}")
    
    for row in context.table:
        todo_id = str(row['id']).strip()
        
        if todo_id in existing_todos:
            print(f"Todo with ID {todo_id} already exists")
            continue
            
        todo_data = {
            "title": row['title'].strip('"'),
            "doneStatus": row['doneStatus'] == 'true' or row['doneStatus'] == 'True',
            "description": row['description'].strip('"')
        }
        
        create_url = f"{context.base_url}/todos/{todo_id}"
        print(f"Creating todo with ID {todo_id}: {todo_data}")
        
        response = requests.post(create_url, json=todo_data)
        
        if response.status_code in [200, 201]:
            context.test_data['todos'].append(todo_id)
            print(f"Successfully created todo with ID {todo_id}")
        else:
            print(f"Failed to create todo with ID {todo_id}. Status: {response.status_code}")
            print(f"Response: {response.text}")
            assert False, f"Failed to create test todo with ID {todo_id}"

@given('a ToDo with ID equal to {id} does not exist or the ID format is invalid')
def step_verify_todo_nonexistent(context, id):
    if not id.isdigit():
        print(f"ID {id} is not a valid numeric format")
        return
        
    response = requests.get(f"{context.base_url}/todos/{id}")
    
    if response.status_code == 200:
        delete_response = requests.delete(f"{context.base_url}/todos/{id}")
        assert delete_response.status_code in [200, 204], f"Failed to delete todo with ID {id}"
        print(f"Deleted existing todo with ID {id} for test setup")

@then('the response JSON should contain a todo with id "{id}"')
def step_verify_todo_id(context, id):
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'todos' in context.response_data:
        todos = context.response_data['todos']
        found = False
        for todo in todos:
            if str(todo.get('id')) == id:
                found = True
                break
        assert found, f"No todo with ID {id} found in response"
    elif isinstance(context.response_data, dict) and 'id' in context.response_data:
        assert_that(str(context.response_data.get('id')), equal_to(id))
    else:
        assert False, f"Response doesn't contain a todo with ID {id}: {context.response_data}"
    
    print(f"Verified response contains todo with ID {id}")