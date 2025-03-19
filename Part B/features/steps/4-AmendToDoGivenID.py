import json
import requests
from behave import given, when, then
from hamcrest import assert_that, equal_to
from features.steps.test_utils import setup_test_todos, get_mapped_id, parse_todo_from_response

@given('the server is running')
def step_verify_server_running(context):
    if not hasattr(context, 'id_mapping'):
        context.id_mapping = {}
        
    url = context.base_url + "/todos"
    response = requests.get(url)
    assert response.status_code == 200, f"API returned status {response.status_code}, server may not be running"
    print("Server is running and API is accessible")

@given('a ToDo with ID equal to {id} exists with title "{title}", doneStatus {doneStatus}, and description "{description}"')
def step_ensure_todo_exists_with_details(context, id, title, doneStatus, description):
    todo_data = {
        "title": title,
        "doneStatus": doneStatus == "true" or doneStatus == "True",
        "description": description
    }
    
    create_response = requests.post(f"{context.base_url}/todos", json=todo_data)
    
    if create_response.status_code in [200, 201]:
        created_todo = create_response.json()
        actual_id = created_todo.get('id')
        
        if not hasattr(context, 'id_mapping'):
            context.id_mapping = {}
        context.id_mapping[id] = actual_id
        
        context.test_data['todos'].append(actual_id)
        print(f"Created todo with actual ID {actual_id} for requested ID {id}")
    else:
        assert False, f"Failed to create test ToDo with ID {id}"

@given('a ToDo with ID equal to {id} exists')
def step_ensure_todo_exists(context, id):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"ToDo with ID {actual_id} does not exist"
    print(f"Verified ToDo with ID {actual_id} exists")
    
    try:
        context.original_todo = response.json()
        print(f"Captured original ToDo state: {context.original_todo}")
    except json.JSONDecodeError:
        assert False, f"Invalid JSON response when getting ToDo {actual_id}"

@given('a ToDo with ID equal to {id} does not exist')
def step_ensure_todo_does_not_exist(context, id):
    url = f"{context.base_url}/todos/{id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        delete_response = requests.delete(url)
        assert delete_response.status_code in [200, 204], f"Failed to delete ToDo with ID {id}"
        print(f"Deleted existing ToDo with ID {id}")
    
    response = requests.get(url)
    assert response.status_code == 404, f"ToDo with ID {id} still exists"
    print(f"Verified ToDo with ID {id} does not exist")

@when('the user requests to update the ToDo with id {id} setting title to "{title}", doneStatus to {doneStatus}, and description to "{description}"')
def step_update_todo_full(context, id, title, doneStatus, description):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    
    update_data = {
        "title": title,
        "doneStatus": doneStatus == "true" or doneStatus == "True",
        "description": description
    }
    
    print(f"Updating ToDo {actual_id} with: {update_data}")
    context.response = requests.put(url, json=update_data)
    
    print(f"Update response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('the user requests to update the ToDo with id {id} setting only description to "{description}"')
def step_update_todo_partial(context, id, description):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    
    original_todo = parse_todo_from_response(context.original_todo, actual_id)
    
    update_data = {
        "title": original_todo.get('title'),
        "doneStatus": original_todo.get('doneStatus') == 'true' or original_todo.get('doneStatus') == True,
        "description": description
    }
    
    print(f"Partially updating ToDo {actual_id} with: {update_data}")
    context.response = requests.put(url, json=update_data)
    
    print(f"Update response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('the user requests to update the ToDo with id {id} setting title to "{title}"')
def step_update_todo_invalid(context, id, title):
    url = f"{context.base_url}/todos/{id}"
    
    update_data = {
        "title": title
    }
    
    print(f"Attempting to update non-existent ToDo {id} with: {update_data}")
    context.response = requests.put(url, json=update_data)
    
    print(f"Update response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@then('the ToDo with id {id} is updated with title "{title}", doneStatus {doneStatus}, and description "{description}"')
def step_verify_todo_updated(context, id, title, doneStatus, description):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to get updated ToDo with ID {actual_id}"
    
    try:
        todo_data = response.json()
        todo = parse_todo_from_response(todo_data, actual_id)
            
        assert todo is not None, f"Could not find Todo with ID {actual_id} in response"
        assert_that(todo.get('title'), equal_to(title))
        assert_that(str(todo.get('doneStatus')).lower(), equal_to(doneStatus.lower()))
        assert_that(todo.get('description'), equal_to(description))
        
        print(f"Verified ToDo {actual_id} was updated with correct values")
    except (json.JSONDecodeError, AssertionError) as e:
        assert False, f"Failed to verify ToDo update: {e}"

@then('the ToDo with id {id} retains its original title and doneStatus, and the description is updated to "{description}"')
def step_verify_todo_partially_updated(context, id, description):
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/todos/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to get updated ToDo with ID {actual_id}"
    
    try:
        todo_data = response.json()
        todo = parse_todo_from_response(todo_data, actual_id)
            
        assert todo is not None, f"Could not find Todo with ID {actual_id} in response"
        
        original = parse_todo_from_response(context.original_todo, actual_id)
            
        assert original is not None, f"Could not find original Todo with ID {actual_id}"
        
        assert_that(todo.get('title'), equal_to(original.get('title')))
        assert_that(str(todo.get('doneStatus')).lower(), equal_to(str(original.get('doneStatus')).lower()))
        assert_that(todo.get('description'), equal_to(description))
        
        print(f"Verified ToDo {actual_id} retained original title and doneStatus with updated description")
    except (json.JSONDecodeError, AssertionError) as e:
        assert False, f"Failed to verify ToDo partial update: {e}"

@then('the user is notified of the completion of the update operation')
def step_verify_update_success(context):
    assert context.response.status_code in [200, 201, 204], \
        f"Expected successful status code, got {context.response.status_code}"
    print("Verified update operation completed successfully")

@then('the user is notified of the non-existence error with a message "{message}"')
def step_verify_error_message(context, message):
    assert context.response.status_code == 404, f"Expected 404 status code, got {context.response.status_code}"
    
    try:
        if context.response_data:
            if isinstance(context.response_data, dict) and 'errorMessages' in context.response_data:
                error_messages = context.response_data['errorMessages']
                error_text = ' '.join(error_messages)
                assert "Invalid GUID" in error_text or message in error_text, \
                    f"Error message '{message}' or 'Invalid GUID' not found in errorMessages: {error_messages}"
            elif 'error' in context.response_data:
                assert message in str(context.response_data['error']) or "Invalid GUID" in str(context.response_data['error']), \
                    f"Error message not found in error: {context.response_data['error']}"
            else:
                response_text = json.dumps(context.response_data)
                assert message in response_text or "Invalid GUID" in response_text, \
                    f"Error message not found in response: {response_text}"
        else:
            assert message in context.response.text or "Invalid GUID" in context.response.text, \
                f"Error message not found in response text"
        
        print(f"Verified error message found in response")
    except (AssertionError) as e:
        assert False, f"Failed to verify error message: {e}"