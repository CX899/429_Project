"""
Common step definitions shared across feature files.
"""
import json
import requests
from behave import given, when, then
from hamcrest import assert_that, equal_to

@given('the system is running')
def step_verify_system_running(context):
    url = context.base_url + "/todos"
    response = requests.get(url)
    assert response.status_code == 200, f"API returned status {response.status_code}, system may not be running"
    print("System is running and API is accessible")

@when('the user sends a GET request to "{endpoint}"')
def step_send_get_request(context, endpoint):
    if endpoint.startswith('/todos/') and hasattr(context, 'id_mapping'):
        parts = endpoint.split('/')
        if len(parts) >= 3 and parts[2].isdigit():
            requested_id = parts[2]
            if requested_id in context.id_mapping:
                actual_id = context.id_mapping[requested_id]
                endpoint = f"/todos/{actual_id}"
                print(f"Mapped endpoint from {'/'.join(parts)} to {endpoint}")
    
    url = context.base_url + endpoint
    context.response = requests.get(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")
        

@when('the user sends a {method} request to "{endpoint}"')
def step_send_request_with_method(context, method, endpoint):
    url = context.base_url + endpoint
    context.response = getattr(requests, method.lower())(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:100]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('the user sends a POST request to "{endpoint}" with this JSON body')
def step_send_post_request_with_json(context, endpoint):
    url = context.base_url + endpoint
    headers = {"Content-Type": "application/json"}
    
    context.response = requests.post(url, json=context.todo_body, headers=headers)
    
    print(f"POST to {url}")
    print(f"Request body: {context.todo_body}")
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('the user sends a POST request to "{endpoint}" with this invalid body')
def step_send_post_request_with_invalid_json(context, endpoint):
    step_send_post_request_with_json(context, endpoint)

@then('the response status should be {status:d}')
def step_verify_status_code(context, status):
    assert_that(context.response.status_code, equal_to(status))

@then('the response JSON should contain an error message mentioning "{message}"')
def step_verify_error_message_contains(context, message):
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
    
    if context.response_data is None:
        assert message in context.response.text, f"Response does not contain error message: {message}"
        print(f"Verified error message in text response contains: {message}")
    else:
        if 'errorMessages' in context.response_data and isinstance(context.response_data['errorMessages'], list):
            error_messages = context.response_data['errorMessages']
            found = False
            for error in error_messages:
                if message in error:
                    found = True
                    break
            assert found, f"Error message does not contain: {message}. Got: {error_messages}"
        elif 'error' in context.response_data:
            assert message in str(context.response_data['error']), \
                f"Error message does not contain: {message}. Got: {context.response_data['error']}"
        else:
            response_text = json.dumps(context.response_data)
            assert message in response_text, f"Response does not contain: {message}. Got: {response_text}"
        
        print(f"Verified error message contains: {message}")

@then('the response JSON should contain an error message "{message}"')
def step_verify_error_message_exact(context, message):
    step_verify_error_message_contains(context, message)

@then('the response contains a list of todos')
def step_verify_todos_list(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'todos' in context.response_data:
        todos = context.response_data['todos']
    else:
        todos = context.response_data
    
    assert isinstance(todos, list), f"Expected a list of todos, but got {type(todos)}"
    
    print(f"Response contains {len(todos)} todos")
    if len(todos) > 0:
        print(f"First todo: {todos[0]}")

@then('the response JSON should contain an error message indicating invalid input')
def step_verify_error_for_invalid_input(context):
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
    
    if context.response_data is None:
        assert "error" in context.response.text.lower() or "invalid" in context.response.text.lower(), \
            f"Response does not contain an error message"
        print("Verified error message in response text")
    else:
        if isinstance(context.response_data, dict) and 'errorMessages' in context.response_data:
            error_messages = context.response_data['errorMessages']
            assert len(error_messages) > 0, "No error messages found in response"
            print(f"Found error messages: {error_messages}")
        elif 'error' in context.response_data:
            assert context.response_data['error'], "Empty error message in response"
            print(f"Found error message: {context.response_data['error']}")
        else:
            response_text = json.dumps(context.response_data)
            assert "error" in response_text.lower() or "invalid" in response_text.lower(), \
                f"Response does not contain error message: {response_text}"
            print("Verified error message in response JSON")