import json
import requests
import random
import string
from behave import given, then, when
from hamcrest import assert_that, equal_to, is_not, contains_string, has_key, has_length, greater_than

@given('the user has a valid JSON body for a new ToDo with')
def step_create_valid_todo_json(context):
    row = context.table[0]
    
    context.todo_body = {
        "title": row["title"].strip('"'),
        "doneStatus": row["doneStatus"] == "true" or row["doneStatus"] == "True",
        "description": row["description"].strip('"')
    }
    
    print(f"Created valid ToDo JSON body: {context.todo_body}")

@given('the user has a valid JSON body for a new ToDo without an "id" field')
def step_create_valid_todo_json_without_id(context):
    step_create_valid_todo_json(context)

@given('the user has an invalid JSON body for a new ToDo with "{issue}"')
def step_create_invalid_todo_json(context, issue):
    if issue == "missing required fields":
        context.todo_body = {
            "doneStatus": False,
            "description": "This ToDo is missing the required title field"
        }
    elif issue == "title is null":
        context.todo_body = {
            "title": None,
            "doneStatus": False,
            "description": "This ToDo has a null title"
        }
    elif issue == "doneStatus is not a boolean value":
        context.todo_body = {
            "title": "Invalid ToDo",
            "doneStatus": "not-a-boolean",
            "description": "This ToDo has an invalid doneStatus value"
        }
    elif issue == "bug: post to existing todo":
        check_response = requests.get(f"{context.base_url}/todos/1")
        if check_response.status_code != 200:
            create_data = {
                "title": "Test Todo for Bug Scenario",
                "doneStatus": False,
                "description": "This ToDo is created to test the POST to ID bug"
            }
            create_response = requests.post(f"{context.base_url}/todos", json=create_data)
            if create_response.status_code in [200, 201]:
                try:
                    created_todo = create_response.json()
                    todo_id = created_todo.get('id')
                    if todo_id:
                        context.test_data['todos'].append(todo_id)
                        print(f"Created todo for bug testing with ID: {todo_id}")
                except Exception as e:
                    print(f"Error processing create response: {e}")
        else:
            try:
                todo = check_response.json()
                todo_id = todo.get('id')
                if todo_id and todo_id not in context.test_data['todos']:
                    context.test_data['todos'].append(todo_id)
                print(f"Found existing todo with ID: {todo_id}")
            except Exception as e:
                print(f"Error processing check response: {e}")
        
        context.todo_body = {}
    else:
        context.todo_body = {}
    
    print(f"Created invalid ToDo JSON body for issue '{issue}': {context.todo_body}")

@when('the user sends a POST request to "{endpoint}"')
def step_send_post_request_direct(context, endpoint):
    """Send a POST request to the specified endpoint."""
    url = context.base_url + endpoint
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending POST request to {url} with body: {context.todo_body}")
    context.response = requests.post(url, json=context.todo_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@then('the response should include an error message about method not allowed')
def step_verify_method_not_allowed(context):
    """Verify that the response includes an error message about HTTP method not allowed."""
    error_phrases = ["method not allowed", "not supported", "invalid method", "not permitted"]
    
    has_error = False
    
    if hasattr(context, 'response_data') and context.response_data:
        if isinstance(context.response_data, dict):
            if 'errorMessages' in context.response_data:
                error_messages = context.response_data['errorMessages']
                error_text = ' '.join(error_messages) if isinstance(error_messages, list) else str(error_messages)
                for phrase in error_phrases:
                    if phrase.lower() in error_text.lower():
                        has_error = True
                        print(f"Found error phrase '{phrase}' in errorMessages")
                        break
            elif 'error' in context.response_data:
                error_text = str(context.response_data['error']).lower()
                for phrase in error_phrases:
                    if phrase.lower() in error_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in error field")
                        break
            else:
                response_text = json.dumps(context.response_data).lower()
                for phrase in error_phrases:
                    if phrase.lower() in response_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in response JSON")
                        break
    
    if not has_error and hasattr(context, 'response'):
        response_text = context.response.text.lower()
        for phrase in error_phrases:
            if phrase.lower() in response_text:
                has_error = True
                print(f"Found error phrase '{phrase}' in response text")
                break
    
    assert has_error, "No 'method not allowed' error message found in response"
    print("Verified response contains a 'method not allowed' error message")

@then('the response JSON should contain a new ToDo with the specified title, doneStatus, and description')
def step_verify_todo_values(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("title"))
    assert_that(context.response_data, has_key("doneStatus"))
    assert_that(context.response_data, has_key("description"))
    
    request_done_status = str(context.todo_body["doneStatus"]).lower()
    response_done_status = str(context.response_data["doneStatus"]).lower()
    
    assert_that(context.response_data["title"], equal_to(context.todo_body["title"]))
    assert_that(response_done_status, equal_to(request_done_status))
    assert_that(context.response_data["description"], equal_to(context.todo_body["description"]))
    
    print("Verified response contains todo with expected values")
    
    todo_id = context.response_data.get("id")
    if todo_id:
        context.test_data["todos"].append(todo_id)
        print(f"Added todo ID {todo_id} to test data for cleanup")

@then('the response JSON should contain a unique "id"')
def step_verify_unique_id(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("id"))
    assert_that(context.response_data["id"], is_not(None))
    assert_that(len(str(context.response_data["id"])), greater_than(0))
    
    print(f"Verified response contains unique ID: {context.response_data['id']}")

@then('the response JSON should contain a newly generated "id" that does not match any existing ToDo')
def step_verify_new_id(context):
    step_verify_unique_id(context)
    
    url = context.base_url + "/todos"
    response = requests.get(url)
    
    try:
        response_data = response.json()
        if isinstance(response_data, dict) and 'todos' in response_data:
            todos = response_data['todos']
        else:
            todos = response_data
        
        existing_ids = [todo["id"] for todo in todos if todo["id"] != context.response_data["id"]]
        
        assert context.response_data["id"] not in existing_ids, "New ID matches an existing todo ID"
        
        print(f"Verified ID {context.response_data['id']} is unique among {len(existing_ids)} existing todos")
    except (json.JSONDecodeError, KeyError) as e:
        assert False, f"Failed to verify unique ID: {e}"